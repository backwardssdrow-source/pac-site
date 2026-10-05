"""Verify the current 15-page MakeGood review, locally or after publication."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit
import os,json,time,urllib.request,threading,functools,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(os.environ.get('MAKEGOOD_ROOT','.')).resolve();SITE=ROOT/'makegood'
M=json.loads((SITE/'site-manifest.json').read_text());REV=M['revision']
LOCAL=os.environ.get('MAKEGOOD_LOCAL')=='1';REPORT=ROOT/os.environ.get('MAKEGOOD_REPORT','makegood-verification');REPORT.mkdir(exist_ok=True)
if LOCAL:
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start();BASE=f'http://127.0.0.1:{server.server_port}/makegood/'
else:BASE='https://backwardssdrow-source.github.io/pac-site/makegood/'
R={'revision':REV,'base':BASE,'pages':[],'checks':[],'source_files_matched':[]}
def fetch(path):
 with urllib.request.urlopen(BASE+path+'?release='+REV,timeout=30) as r:
  assert r.status==200,(path,r.status)
  return r.read()
if not LOCAL:
 deadline=time.monotonic()+420
 while True:
  try:
   if json.loads(fetch('site-manifest.json'))['revision']==REV:break
  except Exception as e:print('Waiting for release:',e,flush=True)
  if time.monotonic()>deadline:raise TimeoutError(REV)
  time.sleep(12)
 def match(path):
  expected=(SITE/path).read_bytes()
  for attempt in range(8):
   if fetch(path)==expected:return path
   time.sleep(8)
  raise AssertionError('Live bytes differ: '+path)
 with ThreadPoolExecutor(max_workers=6) as pool:R['source_files_matched']=list(pool.map(match,M['pages']+['site.css','site.js','makegood-sunrise.svg']))
with sync_playwright() as pw:
 opts={'headless':True}
 if os.environ.get('CHROMIUM_PATH'):opts['executable_path']=os.environ['CHROMIUM_PATH']
 browser=pw.chromium.launch(**opts);page=browser.new_page();errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 if LOCAL:page.route('https://fonts.googleapis.com/**',lambda r:r.fulfill(status=200,content_type='text/css',body=''))
 axe=ROOT/'node_modules/axe-core/axe.min.js'
 for w in [1440,390,320]:
  page.set_viewport_size({'width':w,'height':1000 if w==1440 else 844})
  for route in M['pages']:
   resp=page.goto(BASE+route+'?release='+REV,wait_until='load');assert resp.status==200,route
   page.evaluate('document.fonts.ready')
   assert page.locator('h1').count()==1,route
   assert page.title()==M['expected'][route]['title'],route
   assert page.locator('meta[name="robots"]').get_attribute('content')=='noindex,nofollow'
   assert page.locator('.footer-links a').count()==6,route
   assert page.locator('.review-bar').count()==0
   assert page.locator('img').evaluate_all('(xs)=>xs.every(x=>x.complete&&x.naturalWidth>0)'),route
   dim=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');assert dim['scroll']<=w+1,(route,w,dim)
   got=page.locator('main').evaluate('(x)=>getComputedStyle(x).backgroundColor')
   h=M['expected'][route]['background_hex'].lstrip('#');want='rgb('+', '.join(str(int(h[i:i+2],16)) for i in (0,2,4))+')';assert got==want,(route,got,want)
   controls=page.locator('.footer-links a').evaluate_all('(xs)=>xs.map(x=>({weight:getComputedStyle(x).fontWeight,h:x.getBoundingClientRect().height,w:x.getBoundingClientRect().width}))')
   assert all(x['weight']=='500' and x['h']>=24 and x['w']>=24 for x in controls)
   violations=[];ran=False
   if axe.exists() and w in [1440,390]:
    page.add_script_tag(path=str(axe));result=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})")
    violations=[{'id':v['id'],'impact':v['impact'],'nodes':[n['target'] for n in v['nodes']]} for v in result['violations']];ran=True
    assert not violations,(route,w,violations)
   R['pages'].append({'route':route,'width':w,'overflow':False,'background':got,'automated_accessibility_run':ran,'violations':violations})
   if route in ['index.html','services.html','about.html'] and w in [1440,390]:page.screenshot(path=str(REPORT/(str(w)+'-'+route+'.png')),full_page=True)
  print('Checked 15 pages at',w,flush=True)
 page.set_viewport_size({'width':1440,'height':1000});page.goto(BASE+'index.html')
 assert page.locator('[data-home-audience]').evaluate_all('(xs)=>xs.map(x=>x.dataset.homeAudience)')==['erg','presence','individual']
 colors=page.locator('.home-paths .path-card').evaluate_all('(xs)=>xs.map(x=>getComputedStyle(x).borderTopColor)')
 assert colors==['rgb(240, 68, 28)','rgb(242, 166, 162)','rgb(244, 172, 12)'],colors
 assert '[XX] years' in page.locator('#experience').inner_text()
 assert not any(x in page.locator('main').inner_text() for x in ['LT Peterson','Uber','LT and Travis'])
 assert page.locator('.brand-stage').evaluate('(x)=>getComputedStyle(x).backgroundColor')=='rgb(250, 247, 242)'
 assert page.locator('.site-header').evaluate('(x)=>getComputedStyle(x).position')=='sticky'
 R['checks'].append('Approved homepage copy, placeholders, cream logo panel, sticky header and orange/pink/gold order')
 page.goto(BASE+'services.html?category=erg')
 assert page.locator('[data-filter="erg"]').get_attribute('aria-pressed')=='true'
 assert page.locator('.offer:not([hidden])').count()==5
 page.locator('[data-filter="presence"]').click();assert page.locator('.offer:not([hidden])').count()==4
 assert 'category=presence' in page.url
 page.locator('[data-filter="individual"]').click();assert page.locator('.offer:not([hidden])').count()==1
 page.locator('[data-filter="all"]').click();assert page.locator('.offer:not([hidden])').count()==9
 assert '$' not in page.locator('main').inner_text()
 R['checks'].append('All audience filters, shareable URLs and value-first service overview')
 # Every internal path and anchor must resolve to an existing generated page.
 for route in M['pages']:
  page.goto(BASE+route)
  for href in page.locator('a[href]').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href"))'):
   u=urlsplit(urljoin(BASE+route,href))
   if not (u.netloc==urlsplit(BASE).netloc and u.path.startswith(urlsplit(BASE).path)):continue
   target=u.path[len(urlsplit(BASE).path):] or 'index.html';assert target in M['pages'],(route,href)
   if u.fragment:assert ('id="'+u.fragment+'"') in (SITE/target).read_text(),(route,href)
 R['checks'].append('Every internal page and fragment link resolves')
 page.goto(BASE+'services/senior-presence-advisory.html');page.locator('.detail-summary .button').click()
 assert page.locator('#service-select').input_value()=='senior-presence-advisory'
 sent=[];page.on('request',lambda r:sent.append(r.url) if r.method not in ['GET','HEAD'] else None)
 page.locator('input[name=name]').fill('Review check');page.locator('input[name=email]').fill('test@example.com');page.locator('textarea').fill('Non-sending review check')
 page.locator('[data-preview-submit]').click();assert page.locator('#inquiry-result').is_visible();assert 'NOT SENT' in page.locator('#inquiry-text').inner_text();assert not sent
 R['checks'].append('Service selection and non-sending contact draft')
 page.goto(BASE+'faq.html#terms');assert page.locator('#terms').get_attribute('open') is not None
 page.goto(BASE+'about.html');assert 'Bio coming soon.' in page.locator('main').inner_text()
 page.set_viewport_size({'width':390,'height':844});page.goto(BASE+'index.html');page.locator('.menu-toggle').click();assert page.locator('#navigation').is_visible();page.keyboard.press('Escape');assert page.locator('.menu-toggle').get_attribute('aria-expanded')=='false'
 page.goto(BASE+'services/senior-presence-advisory.html')
 y=[page.locator(s).bounding_box()['y'] for s in ['.detail-intro-block','.detail-summary','.detail-body']];assert y==sorted(y)
 R['checks'].append('FAQ anchors, Travis placeholder, mobile menu/Escape and mobile base-price order')
 for route in ['index.html','services.html','approach.html','services/senior-presence-advisory.html']:
  page.goto(BASE+route);page.add_style_tag(content='html{font-size:200%!important}');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),route
  page.goto(BASE+route);page.add_style_tag(content='*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),route
 R['checks'].append('Selected pages reflow with enlarged text and custom text spacing')
 # No JavaScript: form controls stay disabled and cannot transmit a query string.
 c=browser.new_context(java_script_enabled=False);p=c.new_page();p.goto(BASE+'contact.html');assert p.locator('[data-preview-submit]').is_disabled();assert p.locator('input[name=email]').is_disabled();c.close()
 assert not errors,errors
 browser.close()
R['status']='passed';(REPORT/'report.json').write_text(json.dumps(R,indent=2));print('PASSED',REV,flush=True)
if LOCAL:server.shutdown()
