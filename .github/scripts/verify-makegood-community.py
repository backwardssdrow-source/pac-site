"""Regression checks for community-first copy and accessible category deep links."""
import functools,json,os,re,threading,time,urllib.request
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];SITE=ROOT/'makegood'
REV='20261009-community-pathways-1'
OUT=ROOT/os.environ.get('MAKEGOOD_COMMUNITY_REPORT','community-verification');OUT.mkdir(parents=True,exist_ok=True)
M=json.loads((SITE/'site-manifest.json').read_text())
R={'revision':REV,'status':'running','pages':[],'links':[],'checks':[]}
LOCAL=os.environ.get('MAKEGOOD_LOCAL')=='1';server=None
if LOCAL:
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 BASE=f'http://127.0.0.1:{server.server_port}/makegood/'
else:BASE='https://backwardssdrow-source.github.io/pac-site/makegood/'
R['base']=BASE

def dimensions(page):
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
def run(pw,engine):
 browser=getattr(pw,engine).launch(headless=True)
 context=browser.new_context();page=context.new_page();page.set_default_timeout(15000)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 axe=ROOT/'node_modules/axe-core/axe.min.js'
 for width in ([1440,768,390,320] if engine=='chromium' else [390,320]):
  page.set_viewport_size({'width':width,'height':900 if width>900 else 844})
  for route in M['pages']:
   response=page.goto(BASE+route+'?review='+REV,wait_until='load')
   assert response.status in [200,304],(route,response.status)
   page.evaluate('document.fonts.ready');dimensions(page)
   assert page.locator('h1').count()==1
   ids=page.locator('[id]').evaluate_all('(xs)=>xs.map(x=>x.id)');assert len(ids)==len(set(ids)),route
   assert page.locator('body').evaluate('(e)=>getComputedStyle(e).fontSize')=='18px'
   if engine=='chromium' and width in [1440,390] and axe.exists():
    page.add_script_tag(path=str(axe))
    results=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})")
    assert not results['violations'],(route,width,results['violations'])
   if route in ['index.html','services.html','about.html','approach.html']:
    page.locator('details').evaluate_all('(xs)=>xs.forEach(x=>x.open=true)')
    s=page.add_style_tag(content='html{font-size:200%!important}');dimensions(page);s.evaluate('(e)=>e.remove()')
    s=page.add_style_tag(content='*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}');dimensions(page);s.evaluate('(e)=>e.remove()')
    page.locator('details').evaluate_all('(xs)=>xs.forEach(x=>x.open=false)')
   if route=='about.html':
    order=page.locator('main>section').evaluate_all('(xs)=>xs.map(x=>x.id)')
    assert order.index('experience')<order.index('founders'),order
    assert page.locator('#founders>.founder-grid>.founder-card').count()==2
    assert 'community building, organizational strategy, and investigations' in page.locator('.about-intro').inner_text()
   if route=='services.html':
    assert page.locator('.service-guide-option').count()==4 and page.locator('.offer').count()==9
    assert 'leaders and teams' in page.locator('.service-guide-option').nth(2).inner_text()
    assert 'not event logistics or production' in page.locator('.section-intro').inner_text().replace('—',' ')
   if route=='index.html':
    assert page.locator('img[src*="founder"]').count()==0
    assert 'Community people want to be part of.' in page.locator('main').inner_text()
    assert '39 years' not in page.locator('main').inner_text()
   if engine=='chromium' and width in [1440,390] and route in ['services.html','about.html','approach.html']:
    page.evaluate('scrollTo(0,0)');page.screenshot(path=str(OUT/f'{width}-{route}.png'),full_page=True)
    if route=='services.html':page.locator('#find-your-fit').screenshot(path=str(OUT/f'{width}-chooser.png'))
   R['pages'].append({'engine':engine,'width':width,'route':route,'overflow':False})
  print('Checked',engine,width,flush=True)
 page.set_viewport_size({'width':390,'height':844})
 for category,anchor,count in [('erg','erg-services-heading',5),('presence','leadership-services-heading',4)]:
  page.goto(BASE+'index.html')
  with page.expect_navigation(wait_until='load'):
   page.locator(f'.home-service[data-home-audience={category}] a').click()
  assert urlsplit(page.url).fragment==anchor
  assert page.locator('.offer:visible').count()==count
  heading=page.locator('#'+anchor);assert heading.is_visible()
  assert -1<=heading.bounding_box()['y']<160,(engine,heading.bounding_box())
  assert heading.evaluate('(e)=>e===document.activeElement')
  R['links'].append({'engine':engine,'from':'Home','category':category,'target':anchor,'visible_offers':count,'focused':True})
  if engine=='chromium':page.screenshot(path=str(OUT/f'mobile-{category}-arrival.png'))
  page.go_back(wait_until='load');assert urlsplit(page.url).path.endswith('/index.html')
 page.goto(BASE+'services.html')
 with page.expect_navigation(wait_until='load'):
  page.locator('.service-guide-option a').nth(2).click()
 assert page.locator('.offer:visible').count()==4
 for category,anchor,count in [('erg','erg-services-heading',5),('individual','coaching-services-heading',1),('all','service-options-heading',9)]:
  b=page.locator(f'[data-filter={category}]');b.focus();page.keyboard.press('Enter')
  assert b.evaluate('(e)=>e===document.activeElement')
  assert urlsplit(page.url).fragment==anchor
  assert page.locator('.offer:visible').count()==count
  page.reload(wait_until='load')
  assert page.locator('#'+anchor).is_visible() and page.locator('.offer:visible').count()==count
 page.goto(BASE+'approach.html')
 summary=page.locator('.process-card .more summary').first;summary.focus();page.keyboard.press('Enter')
 assert page.locator('.approach-example').is_visible()
 assert 'Illustrative scenario—not a client case study.' in page.locator('.approach-example').inner_text()
 if engine=='chromium':page.locator('.process-card').first.screenshot(path=str(OUT/'mobile-approach-example.png'))
 page.keyboard.press('Enter');assert not page.locator('.approach-example').is_visible()
 context.close()
 nojs=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
 q=nojs.new_page();q.goto(BASE+'index.html');q.locator('.home-service[data-home-audience=presence] a').click()
 assert urlsplit(q.url).fragment=='leadership-services-heading'
 assert q.locator('#leadership-services-heading').is_visible() and q.locator('.offer').count()==9
 R['links'].append({'engine':engine,'javascript':False,'native_heading_link':True})
 nojs.close();browser.close();assert not errors,errors
try:
 assert M.get('editorial_revision')==REV
 for p in SITE.rglob('*'):
  if p.suffix in ['.html','.js']:
   assert not re.search(r'[\w.+-]+@makegoodco\.com',p.read_text(),re.I),'Private recipient in public source'
 if not LOCAL:
  paths=['index.html','services.html','about.html','approach.html','service-navigation.js','site-manifest.json']
  for p in paths:
   for attempt in range(24):
    try:
     with urllib.request.urlopen(BASE+p+'?review='+REV,timeout=20) as response:actual=response.read()
     if actual==(SITE/p).read_bytes():break
    except Exception:pass
    time.sleep(8)
   else:raise AssertionError('Published bytes differ: '+p)
  R['published_sources_matched']=paths
 with sync_playwright() as pw:
  run(pw,'chromium')
  if os.environ.get('MAKEGOOD_WEBKIT')=='1':run(pw,'webkit')
 R['status']='passed'
 R['checks']=['All 15 pages render','Four problem-first pathways include leadership','Home links land on filtered results with focus','Filter reloads preserve category and anchor','Native deep links work without JavaScript','About expertise precedes unchanged bios','Illustrative example opens by keyboard','No portrait on Home','No public intake recipient addresses']
 print('PASSED',REV,flush=True)
except Exception as e:R['status']='failed';R['error']=repr(e);raise
finally:
 (OUT/'report.json').write_text(json.dumps(R,indent=2))
 if server:server.shutdown()
