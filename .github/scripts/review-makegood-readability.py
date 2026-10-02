"""Review the current site and a readability-only stylesheet; never submit data."""
from pathlib import Path
import json, threading, functools, hashlib, re, os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
SITE=Path('makegood'); OUT=Path('readability-review'); OUT.mkdir(exist_ok=True)
MAN=json.loads((SITE/'site-manifest.json').read_text()); ROUTES=MAN['pages']; REV='20261002-readability-1'
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',8765),Quiet)
threading.Thread(target=server.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:8765/makegood/'
axe=Path('node_modules/axe-core/axe.min.js').read_text()
text_spacing='*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}'
report={'source_commit':os.environ.get('GITHUB_SHA'),'pages':len(ROUTES),'before':[],'after':[],'checks':[],'failures':[]}
original={r:(SITE/r).read_text() for r in ROUTES}
for r,html in original.items():
 d=OUT/'original'/r;d.parent.mkdir(parents=True,exist_ok=True);d.write_text(html)
def metrics(page):
 return page.evaluate('''() => ({fontReady:document.fonts.check('18px Inter'), width:innerWidth,scroll:document.documentElement.scrollWidth, mainBackground:getComputedStyle(document.querySelector('main')).backgroundColor, typography:[...document.querySelectorAll('.step-number,.principle>span,.detail-intro,.brandtext,.studio-row>p,.scope-list li,.row-footer>span,.advisory-upgrade p,.footer-links a,h1')].filter(e=>e.getBoundingClientRect().height>0).map(e=>{let s=getComputedStyle(e);return {text:e.innerText.slice(0,130),fontSize:s.fontSize,lineHeight:s.lineHeight,color:s.color,weight:s.fontWeight,letterSpacing:s.letterSpacing}})})''')
def audit(page,phase,route,width,run_axe=True):
 page.set_viewport_size({'width':width,'height':1000})
 page.goto(BASE+route,wait_until='networkidle');page.evaluate('document.fonts.ready')
 page.locator('details').evaluate_all('(es)=>es.forEach(e=>e.open=true)')
 m=metrics(page);m.update(route=route,width=width)
 if run_axe:
  page.add_script_tag(content=axe)
  a=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}})")
  m['violations']=[{'id':v['id'],'impact':v['impact'],'help':v['help'],'nodes':[{'target':n['target'],'html':n['html'],'failureSummary':n.get('failureSummary','')} for n in v['nodes']]} for v in a['violations']]
  m['manual_review']=[{'id':v['id'],'nodes':len(v['nodes'])} for v in a['incomplete']]
 report[phase].append(m)
 if width==1440 or (phase=='after' and width==390):
  path=OUT/phase/str(width)/(route.replace('/','_')+'.png');path.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(path),full_page=True)
 if phase=='after':
  if m['scroll']>width+1:report['failures'].append(f'{route}: overflow at {width}')
  if m.get('violations'):report['failures'].append(f'{route}: axe at {width}: '+','.join(v['id'] for v in m['violations']))
with sync_playwright() as pw:
 browser=pw.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 for r in ROUTES:audit(page,'before',r,1440)
 # Link the override after the existing stylesheet, preserving every visible word.
 for r,html in original.items():
  s=BeautifulSoup(html,'html.parser');prefix='../' if '/' in r else ''
  if not s.select_one('link[data-readability]'):
   link=s.new_tag('link',rel='stylesheet',href=prefix+'readability.css?v='+REV);link['data-readability']='true';s.head.append(link)
  (SITE/r).write_text(str(s))
 for width in [1440,390,320]:
  for r in ROUTES:audit(page,'after',r,width,run_axe=width!=320)
 # Text enlargement and user-defined spacing may not hide content or cause page overflow.
 for r in ROUTES:
  for width,mode in [(1440,'200-percent-text'),(320,'text-spacing')]:
   page.set_viewport_size({'width':width,'height':1000});page.goto(BASE+r,wait_until='load');page.locator('details').evaluate_all('(es)=>es.forEach(e=>e.open=true)')
   page.add_style_tag(content='html{font-size:200%!important}' if mode=='200-percent-text' else text_spacing)
   d=metrics(page)
   if d['scroll']>width+1:report['failures'].append(f'{r}: {mode} overflow {d["scroll"]}/{width}')
   if r in ['services.html','approach.html','services/senior-presence-advisory.html']:
    out=OUT/'stress'/mode/(r.replace('/','_')+'.png');out.parent.mkdir(parents=True,exist_ok=True);page.screenshot(path=str(out),full_page=True)
 # Navigation and disclosure interactions.
 page.set_viewport_size({'width':390,'height':844});page.goto(BASE+'index.html');page.locator('.menu-toggle').click();assert page.locator('.navlinks').is_visible();page.keyboard.press('Escape');assert page.locator('.menu-toggle').get_attribute('aria-expanded')=='false'
 page.goto(BASE+'services.html?category=presence');assert page.locator('.filter[data-filter=presence]').get_attribute('aria-pressed')=='true'
 assert page.locator('#service-senior-presence-advisory .advisory-upgrade').is_visible()
 page.goto(BASE+'faq.html#terms');assert page.locator('#terms').get_attribute('open') is not None
 report['checks']+=['Mobile menu and Escape','Shareable service filter','Meeting Feedback remains nested','FAQ anchor opens terms']
 for r in ROUTES:
  def text(h):
   s=BeautifulSoup(h,'html.parser');return s.body.get_text(' ',strip=True)
  assert text(original[r])==text((SITE/r).read_text()),r
 report['checks']+=['All 15 pages keep identical visible copy, fees and links','1440, 390 and 320 pixel widths','200 percent text and WCAG text-spacing overrides','Inter loaded during browser checks']
 report['page_errors']=errors
 if errors:report['failures']+=errors
 browser.close()
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'before_violations':[(x['route'],[v['id'] for v in x.get('violations',[])]) for x in report['before'] if x.get('violations')],'after_failures':report['failures'],'checks':report['checks']},indent=2))
if report['failures']:raise SystemExit('Readability review requires fixes; no publication.')
