"""Scoped browser checks, not a certification of WCAG conformance."""
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import os,json,time,threading,functools,urllib.request
from playwright.sync_api import sync_playwright
ROOT=Path(os.environ.get('MAKEGOOD_ROOT','.')).resolve();S=ROOT/'makegood'
M=json.loads((S/'site-manifest.json').read_text());REV=M['revision']
LOCAL=os.environ.get('MAKEGOOD_LOCAL')=='1'
OUT=ROOT/os.environ.get('MAKEGOOD_REPORT','makegood-verification');OUT.mkdir(parents=True,exist_ok=True)
R={'revision':REV,'status':'running','pages':[],'checks':[],'navigation':[],'source_files_matched':[],'automated_accessibility_checks':0}
server=None
if LOCAL:
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start();BASE=f'http://127.0.0.1:{server.server_port}/makegood/'
else:BASE='https://backwardssdrow-source.github.io/pac-site/makegood/'
R['base']=BASE
PAGES=['index.html','services.html','approach.html','about.html','faq.html','contact.html']
def read(path):
 with urllib.request.urlopen(BASE+path+'?release='+REV,timeout=30) as r:return r.read()
def match(path):
 for i in range(14):
  try:
   if read(path)==(S/path).read_bytes():return path
  except Exception:pass
  time.sleep(8)
 raise AssertionError('Published bytes differ: '+path)
def image_ready(page):
 page.locator('img').evaluate_all('(xs)=>xs.forEach(x=>x.loading="eager")')
 page.wait_for_function('[...document.images].every(x=>x.complete&&x.naturalWidth>0)',timeout=15000)
def dimensions(page,engine,route,width,test):
 data=page.evaluate('''()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,bodyFont:getComputedStyle(document.body).fontSize})''')
 assert data['scroll']<=width+1,(engine,route,test,data)
 assert data['bodyFont']==('36px' if test=='text-200%' else '18px'),(route,test,data)
 R['pages'].append(dict(browser=engine,route=route,test=test,**data))
def run_browser(pw,engine):
 browser=getattr(pw,engine).launch(headless=True)
 page=browser.new_page();page.set_default_timeout(15000);errors=[]
 page.on('pageerror',lambda err:errors.append(str(err)))
 axe=ROOT/'node_modules/axe-core/axe.min.js'
 for width in ([1440,768,430,390,320] if engine=='chromium' else [390,320]):
  page.set_viewport_size({'width':width,'height':900 if width>900 else 844})
  for route in M['pages']:
   response=page.goto(BASE+route+'?release='+REV,wait_until='load');assert response.status==200,(route,response.status)
   page.evaluate('document.fonts.ready');image_ready(page)
   assert page.title()==M['expected'][route]['title'],route
   assert page.locator('h1').count()==1,route
   assert page.locator('meta[name=viewport]').count()==1,route
   assert page.locator('meta[name=robots]').get_attribute('content')=='noindex,nofollow',route
   assert page.locator('meta[name=site-revision]').get_attribute('content')==REV,route
   assert page.locator('body').get_attribute('data-page')==route,route
   ids=page.locator('[id]').evaluate_all('(xs)=>xs.map(x=>x.id)');assert len(ids)==len(set(ids)),route
   dimensions(page,engine,route,width,'normal')
   if width<=900:
    assert page.locator('header').evaluate('(e)=>getComputedStyle(e).position')=='relative',route
    assert page.locator('.menu-toggle').is_visible() and not page.locator('#navigation').is_visible(),route
    assert page.locator('header').bounding_box()['height']<=90,route
   if route=='index.html':
    assert page.locator('main>section').count()==3
    assert page.locator('.home-service').count()==3
    assert '39 years' not in page.locator('main').inner_text()
   if route=='services.html':
    assert page.locator('.service-guide-option').count()==4
    assert page.locator('.offer:visible').count()==9
    assert page.locator('.optional-context').count()==2
    assert page.locator('.optional-context[open]').count()==0
    assert page.locator('.optional-context>summary').count()==2
   if route=='about.html':
    assert page.locator('#founders .founder-grid>.founder-card').count()==2
    assert page.locator('#founders .founder-portrait img').count()==2
   if route=='faq.html':
    assert page.locator('.faq-group-heading').count()==3
    assert page.locator('.faq-list details').count()==10
   controls=page.locator('a.button:visible,.text-link:visible,.service-guide-link:visible,.home-founder-link:visible,.menu-toggle:visible,.filter:visible,.breadcrumbs a:visible,summary:visible,.footer-links a:visible').evaluate_all('(xs)=>xs.map(x=>({text:x.textContent.trim(),h:x.getBoundingClientRect().height,w:x.getBoundingClientRect().width}))')
   assert all(x['h']>=43.9 and x['w']>=24 for x in controls),(route,width,controls)
   if axe.exists() and engine=='chromium' and width in [1440,390]:
    page.add_script_tag(path=str(axe));result=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})")
    violations=[{'id':x['id'],'nodes':[n['target'] for n in x['nodes']]} for x in result['violations']]
    assert not violations,(route,width,violations);R['automated_accessibility_checks']+=1
   if width==390 and route in ['index.html','services.html','about.html','faq.html'] and engine=='chromium':
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/(route.replace('.html','')+'-mobile.png')),full_page=True)
    if route=='services.html':
     page.locator('#find-your-fit').screenshot(path=str(OUT/'service-guide-mobile.png'))
     page.locator('#find-your-fit').scroll_into_view_if_needed();page.screenshot(path=str(OUT/'services-mobile-screen.png'))
   if width in [1440,390,320]:
    page.locator('details').evaluate_all('(xs)=>xs.forEach(x=>x.open=true)')
    style=page.add_style_tag(content='html{font-size:200%!important}')
    dimensions(page,engine,route,width,'text-200%');style.evaluate('(e)=>e.remove()')
    style=page.add_style_tag(content='*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}')
    dimensions(page,engine,route,width,'custom-spacing');style.evaluate('(e)=>e.remove()')
  print('Checked',engine,width,flush=True)
 page.set_viewport_size({'width':390,'height':844});page.goto(BASE+'index.html')
 page.keyboard.press('Tab');assert page.locator('.skip').evaluate('(e)=>e===document.activeElement')
 page.keyboard.press('Enter');assert page.locator('main').evaluate('(e)=>e===document.activeElement')
 for target in PAGES[1:]+PAGES[:1]:
  menu=page.locator('.menu-toggle');menu.focus();page.keyboard.press('Enter');assert menu.get_attribute('aria-expanded')=='true'
  link=page.locator('#navigation a[href="'+target+'"]');link.focus()
  with page.expect_navigation(wait_until='load') as navigation:page.keyboard.press('Enter')
  assert navigation.value.status==200 and navigation.value.request.resource_type=='document'
  assert urlsplit(page.url).path.endswith('/'+target)
  R['navigation'].append({'browser':engine,'javascript':True,'target':target})
 page.locator('.menu-toggle').focus();page.keyboard.press('Enter');page.keyboard.press('Escape')
 assert page.locator('.menu-toggle').get_attribute('aria-expanded')=='false'
 assert page.locator('.menu-toggle').evaluate('(e)=>e===document.activeElement')
 page.goto(BASE+'services.html')
 for el in page.locator('.optional-context>summary').all():
  el.focus();page.keyboard.press('Enter');assert el.evaluate('(e)=>e.parentElement.open');page.keyboard.press('Enter');assert not el.evaluate('(e)=>e.parentElement.open')
 for category,count in [('erg',5),('presence',4),('individual',1),('all',9)]:
  page.locator('[data-filter='+category+']').click();assert page.locator('.offer:visible').count()==count
  assert page.locator('[data-filter='+category+']').get_attribute('aria-pressed')=='true'
 page.goto(BASE+'faq.html#terms');assert page.locator('#terms').get_attribute('open') is not None
 page.goto(BASE+'services/coaching.html');page.locator('.detail-summary .button').click();assert page.locator('#service-select').input_value()=='coaching'
 sent=[];page.on('request',lambda r:sent.append(r.url) if r.method not in ['GET','HEAD'] else None)
 page.locator('input[name=name]').fill('Accessibility check');page.locator('input[name=email]').fill('test@example.com');page.locator('textarea').fill('Non-sending form check.')
 page.locator('[data-preview-submit]').click();assert 'NOT SENT' in page.locator('#inquiry-text').inner_text();assert not sent
 page.emulate_media(reduced_motion='reduce');page.goto(BASE+'services.html')
 assert page.locator('html').evaluate('(e)=>getComputedStyle(e).scrollBehavior')=='auto'
 page.set_viewport_size({'width':844,'height':390});page.locator('.menu-toggle').click()
 assert page.locator('header').evaluate('(e)=>getComputedStyle(e).position')=='relative'
 assert page.locator('#navigation a').evaluate_all('(xs)=>xs.every(x=>x.getBoundingClientRect().height>=44)')
 context=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844});q=context.new_page();q.goto(BASE+'index.html')
 for target in PAGES[1:]+PAGES[:1]:
  assert q.locator('#navigation').is_visible()
  with q.expect_navigation():q.locator('#navigation a[href="'+target+'"]').click()
  assert urlsplit(q.url).path.endswith('/'+target);R['navigation'].append({'browser':engine,'javascript':False,'target':target})
 q.goto(BASE+'services.html');q.locator('.optional-context>summary').first.click();assert q.locator('.optional-context').first.get_attribute('open') is not None
 q.goto(BASE+'contact.html');assert q.locator('[data-preview-submit]').is_disabled()
 context.close();assert not errors,errors;browser.close()
try:
 if not LOCAL:
  with ThreadPoolExecutor(max_workers=6) as pool:R['source_files_matched']=list(pool.map(match,M['pages']+['site.css','site-base.css','home.css','site.js','lt-founder.avif','travis-founder.avif']))
 with sync_playwright() as pw:
  run_browser(pw,'chromium')
  if os.environ.get('MAKEGOOD_WEBKIT')=='1':run_browser(pw,'webkit')
 R['status']='passed';R['checks']=['All 15 separate pages','320 CSS-pixel reflow (400%-zoom equivalent at 1280px)','Text doubles with a 200% root-font preference','Expanded content tolerates custom text spacing','44px standalone controls','Keyboard menu, Escape, skip link and native disclosures','Category filters and service-to-coaching inquiry path','Both founder cards in the correct grid','Reduced-motion and no-JavaScript navigation','Contact remains a non-sending preview'];print('PASSED',REV,flush=True)
except Exception as e:R['status']='failed';R['error']=repr(e);raise
finally:
 (OUT/'report.json').write_text(json.dumps(R,indent=2))
 if server:server.shutdown()
