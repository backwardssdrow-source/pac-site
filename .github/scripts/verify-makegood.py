"""Verify the approved MakeGood release locally or on GitHub Pages."""
from pathlib import Path
import os, json, time, hashlib, urllib.request, functools, threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from playwright.sync_api import sync_playwright

ROOT=Path(os.environ.get('MAKEGOOD_ROOT','.')).resolve()
SITE=ROOT/'makegood'
MANIFEST=json.loads((SITE/'site-manifest.json').read_text())
REV=MANIFEST['revision']
REPORT=ROOT/'makegood-verification';REPORT.mkdir(exist_ok=True)
local=os.environ.get('MAKEGOOD_LOCAL')=='1'
if local:
 class QuietHandler(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(QuietHandler,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 BASE=f'http://127.0.0.1:{server.server_port}/makegood/'
else:BASE='https://backwardssdrow-source.github.io/pac-site/makegood/'

def fetch(path):
 with urllib.request.urlopen(BASE+path+'?release='+REV,timeout=30) as response:
  assert response.status==200,(path,response.status)
  return response.read()

if not local:
 deadline=time.time()+420
 while True:
  try:
   if json.loads(fetch('site-manifest.json'))['revision']==REV:break
  except Exception as error: print('Waiting for published release:',str(error),flush=True)
  if time.time()>deadline:raise RuntimeError('Expected release is not published yet: '+REV)
  time.sleep(12)
 paths=MANIFEST['pages']+['site.css','site.js','makegood-sunrise.svg']
 def matches(path):
  expected=(SITE/path).read_bytes()
  for attempt in range(8):
   actual=fetch(path)
   if actual==expected:return path
   time.sleep(8)
  raise AssertionError('Published bytes differ: '+path)
 with ThreadPoolExecutor(max_workers=6) as pool: list(pool.map(matches,paths))

backgrounds={'cream':'rgb(250, 247, 242)','blush':'rgb(249, 237, 232)','charcoal':'rgb(236, 234, 224)','teal':'rgb(236, 234, 224)','indigo':'rgb(249, 233, 225)','lilac':'rgb(250, 241, 224)','gold':'rgb(250, 241, 224)'}
report={'revision':REV,'base':BASE,'published_byte_matches':not local,'pages':[],'checks':[]}
with sync_playwright() as pw:
 options={'headless':True}
 if os.environ.get('CHROMIUM_PATH'):options['executable_path']=os.environ['CHROMIUM_PATH']
 browser=pw.chromium.launch(**options)
 page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
 for viewport in [{'width':1440,'height':1000},{'width':390,'height':844},{'width':320,'height':900}]:
  page.set_viewport_size(viewport)
  for route in MANIFEST['pages']:
   response=page.goto(BASE+route+'?release='+REV,wait_until='load')
   assert local or (response and response.status==200),route
   if not local:page.evaluate('document.fonts.ready')
   assert page.locator('h1').count()==1,route
   assert page.title()==MANIFEST['expected'][route]['title'],(route,page.title())
   assert page.locator('.footer-links a').count()==6,route
   assert page.locator('.stage-caption, .art-caption').count()==0,route
   assert not page.locator('body').inner_text().find('PREVIEW · NOT LIVE')>=0,route
   dims=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
   assert dims['scroll']<=dims['width']+1,(route,viewport,dims)
   assert page.locator('img').evaluate_all('(xs)=>xs.every(x=>x.complete&&x.naturalWidth>0)'),route
   bg=page.locator('main').evaluate('(x)=>getComputedStyle(x).backgroundColor')
   expected=backgrounds[MANIFEST['expected'][route]['background']]
   assert bg==expected,(route,bg,expected)
   buttons=page.locator('.footer-links a').evaluate_all('(xs)=>xs.map(x=>({weight:getComputedStyle(x).fontWeight,height:x.getBoundingClientRect().height,width:x.getBoundingClientRect().width}))')
   assert all(b['weight']=='500' and b['height']>=24 and b['width']>=24 for b in buttons),(route,buttons)
   if viewport['width']==1440:
    name=route.replace('/','-').replace('.html','.png')
    page.screenshot(path=str(REPORT/name),full_page=True)
    report['pages'].append({'route':route,'background':bg,'footer_buttons':buttons})
  print('Checked all 15 pages at width',viewport['width'],flush=True)
 page.set_viewport_size({'width':1440,'height':1000})
 page.goto(BASE+'services.html?category=erg');page.locator('[data-filter="erg"][aria-pressed="true"]').wait_for()
 assert page.locator('.studio-panel:not([hidden])').count()==1
 assert page.locator('.session-card:not([hidden])').count()==2
 page.locator('[data-filter="presence"]').click()
 assert 'category=presence' in page.url
 page.locator('[data-filter="all"]').click()
 assert page.locator('.studio-panel:not([hidden])').count()==2
 assert page.locator('.session-card:not([hidden])').count()==3
 report['checks'].append('Service filtering and shareable category URLs work')
 page.locator('#service-senior-presence-advisory a').click()
 assert '/services/senior-presence-advisory.html' in page.url
 assert page.locator('h1').inner_text()=='Leadership Advisory'
 page.locator('.detail-summary .button.primary').click()
 assert page.locator('#service-select').input_value()=='senior-presence-advisory'
 report['checks'].append('Service-detail links and inquiry preselection work')
 requests=[];page.on('request',lambda r:requests.append(r) if r.method=='POST' else None)
 page.locator('input[name="name"]').fill('Website verification')
 page.locator('input[name="email"]').fill('test@example.com')
 page.locator('textarea[name="message"]').fill('Local preview test; no inquiry should be sent.')
 page.locator('[data-preview-submit]').click()
 assert page.locator('#inquiry-preview-panel').is_visible()
 assert 'NOT SENT' in page.locator('#inquiry-text').inner_text()
 assert not requests,'Form unexpectedly sent a POST'
 report['checks'].append('Inquiry creates an unsent draft; no network submission')
 page.goto(BASE+'faq.html#terms')
 page.wait_for_function("document.getElementById('terms').open")
 report['checks'].append('Direct FAQ terms link opens its answer')
 page.goto(BASE+'about.html')
 assert 'LT Peterson' in page.locator('main').inner_text()
 assert 'Bio coming soon.' in page.locator('main').inner_text()
 report['checks'].append('Founder bio and Travis placeholder retained')
 page.set_viewport_size({'width':390,'height':844});page.goto(BASE+'index.html')
 page.locator('.menu-toggle').click()
 assert page.locator('#navigation').is_visible()
 page.keyboard.press('Escape')
 assert page.locator('.menu-toggle').get_attribute('aria-expanded')=='false'
 page.locator('.footer-links a[href="about.html"]').click()
 assert '/about.html' in page.url
 report['checks'].append('Mobile navigation, Escape key, and footer navigation work')
 assert not errors,errors
 browser.close()
report['status']='passed'
(REPORT/'report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if local:server.shutdown()
