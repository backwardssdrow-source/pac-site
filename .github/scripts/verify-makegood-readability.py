"""Verify live MakeGood pages against the checked-in release without submitting forms."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, os, time, urllib.request
from playwright.sync_api import sync_playwright
SITE=Path('makegood');OUT=Path('readability-live');OUT.mkdir(exist_ok=True)
ROUTES=json.loads((SITE/'site-manifest.json').read_text())['pages']
BASE='https://backwardssdrow-source.github.io/pac-site/makegood/'
SHA=os.environ.get('GITHUB_SHA','readability')
paths=ROUTES+['site.css','readability.css','site.js','makegood-sunrise.svg']
def verify_bytes(path):
 expected=(SITE/path).read_bytes();last='Not fetched'
 for attempt in range(18):
  try:
   req=urllib.request.Request(BASE+path+'?readability-check='+SHA,headers={'Cache-Control':'no-cache','User-Agent':'MakeGood-Readability-Check'})
   with urllib.request.urlopen(req,timeout=20) as response: actual=response.read()
   if actual==expected:return path
   last='Content differs from release'
  except Exception as error:last=str(error)
  time.sleep(10)
 raise AssertionError(path+': '+last)
with ThreadPoolExecutor(max_workers=6) as pool:verified=list(pool.map(verify_bytes,paths))
axe=Path('node_modules/axe-core/axe.min.js').read_text()
report={'commit':SHA,'source_files_matched':verified,'pages':[],'failures':[],'checks':[]}
with sync_playwright() as pw:
 browser=pw.chromium.launch();page=browser.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
 for width in [1440,390,320]:
  page.set_viewport_size({'width':width,'height':1000})
  for route in ROUTES:
   response=page.goto(BASE+route+'?readability-check='+SHA,wait_until='networkidle');assert response.status==200
   page.evaluate('document.fonts.ready');assert page.locator('link[data-readability]').count()==1
   page.locator('details').evaluate_all('(es)=>es.forEach(e=>e.open=true)')
   dims=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
   if dims['scroll']>width+1:report['failures'].append(route+': horizontal overflow at '+str(width))
   item={'route':route,'width':width,'overflow':dims['scroll']>width+1}
   if width!=320:
    page.add_script_tag(content=axe)
    a=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}})")
    item['violations']=[{'id':v['id'],'nodes':[n['target'] for n in v['nodes']]} for v in a['violations']]
    item['manual_review']=[{'id':v['id'],'nodes':[n['target'] for n in v['nodes']]} for v in a['incomplete']]
    if item['violations'] or item['manual_review']:report['failures'].append(item)
   report['pages'].append(item)
   if route in ['approach.html','services.html','about.html','services/senior-presence-advisory.html'] and width!=320:
    page.screenshot(path=str(OUT/(str(width)+'-'+route.replace('/','_')+'.png')),full_page=True)
 page.goto(BASE+'approach.html?readability-check='+SHA)
 labels=page.locator('.step-number,.principle>span').evaluate_all('(es)=>es.map(e=>({color:getComputedStyle(e).color,size:getComputedStyle(e).fontSize}))')
 assert all(x['color']=='rgb(31, 46, 42)' and float(x['size'][:-2])>=15 for x in labels),labels
 report['checks'].append('Previously low-contrast gold and pink labels use Deep Charcoal at 15px or larger')
 page.goto(BASE+'services.html?readability-check='+SHA)
 sizes=page.locator('.studio-row>p').evaluate_all('(es)=>es.map(e=>getComputedStyle(e).fontSize)');assert all(float(x[:-2])>=18 for x in sizes)
 report['checks'].append('Service reading text renders at 18px or larger')
 page.set_viewport_size({'width':390,'height':844});page.goto(BASE+'index.html?readability-check='+SHA)
 page.locator('.menu-toggle').click();assert page.locator('.navlinks').is_visible();page.keyboard.press('Escape');assert page.locator('.menu-toggle').get_attribute('aria-expanded')=='false'
 report['checks'].append('Mobile menu and Escape work')
 report['page_errors']=errors;report['failures']+=errors
 browser.close()
report['status']='passed' if not report['failures'] else 'failed'
(OUT/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'status':report['status'],'live_page_checks':len(report['pages']),'files_matched':len(verified),'checks':report['checks'],'failures':report['failures']},indent=2))
if report['failures']:raise SystemExit(1)
