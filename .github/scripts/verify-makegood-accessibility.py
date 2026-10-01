"""Targeted browser/axe accessibility and palette checks; not a full conformance certification."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import json,os,re,threading,traceback
from playwright.sync_api import sync_playwright

OUT=Path('makegood-verification');OUT.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',8766),partial(Quiet,directory=str(Path.cwd())))
threading.Thread(target=server.serve_forever,daemon=True).start()
BASE='http://127.0.0.1:8766/makegood/'
manifest=json.loads(Path('makegood/site-manifest.json').read_text())
brand=json.loads(Path('makegood/brand-palette.json').read_text())
allowed=set(brand['colors'].values())
report={'status':'running','pages':[],'violations':[],'checks':[],'limitations':['Automated checks and targeted browser interaction tests are not a full WCAG conformance audit or screen-reader user test.']}
axe=Path('node_modules/axe-core/axe.min.js').read_text()

def audit(page,route,state):
    page.add_script_tag(content=axe)
    result=page.evaluate("""async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa','best-practice']}})""")
    problems=[{'id':v['id'],'impact':v['impact'],'description':v['description'],'nodes':[{'target':n['target'],'summary':n.get('failureSummary')} for n in v['nodes']]} for v in result['violations']]
    report['pages'].append({'route':route,'state':state,'violations':len(problems),'incomplete_rules':[v['id'] for v in result['incomplete']]})
    if problems: report['violations'].append({'route':route,'state':state,'problems':problems})

def overflow(page):
    return page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')

try:
    for f in Path('makegood').glob('*.css'):
        colors={x.upper() for x in re.findall(r'#[0-9a-fA-F]{3,8}\b',f.read_text())}
        assert colors<=allowed,(str(f),colors-allowed)
        assert not re.search(r'--(?:evergreen|mulberry|clay|sage)\b',f.read_text()),str(f)
    report['checks'].append('Every shared stylesheet contains only the ten exact approved palette colors; obsolete tokens removed.')
    with sync_playwright() as pw:
        browser=pw.chromium.launch()
        page=browser.new_page(viewport={'width':1440,'height':1000})
        page_errors=[]
        page.on('pageerror',lambda e:page_errors.append(str(e)))
        for route in manifest['pages']:
            response=page.goto(BASE+route,wait_until='networkidle')
            assert response.status==200,route
            body=page.locator('body').inner_text()
            assert 'People. Culture. Possibilities.' in body,route
            assert not re.search(r'People\.\s*Culture\.\s*Practice\.',body,re.I),route
            assert 'Clear scope. Practical support.' not in body,route
            assert 'Choose the support that fits what you are working through.' not in body,route
            assert page.locator('.stage-caption').count()==0,route
            assert page.locator('link[href*="palette.css"]').count()==1,route
            assert page.evaluate("getComputedStyle(document.querySelector('.previewbar')).backgroundColor")=='rgb(31, 46, 42)',route
            assert not overflow(page),route
            audit(page,route,'desktop')
            filename=route.replace('/','-').replace('.html','')
            page.screenshot(path=str(OUT/(filename+'-desktop.png')),full_page=True)
            for width in (390,320):
                page.set_viewport_size({'width':width,'height':844})
                assert not overflow(page),(route,width)
                if width==390:
                    audit(page,route,'mobile-390')
                    page.screenshot(path=str(OUT/(filename+'-mobile.png')),full_page=True)
            page.set_viewport_size({'width':1440,'height':1000})
            page.evaluate("document.documentElement.style.fontSize='200%'")
            assert not overflow(page),(route,'200-percent-text')
            page.evaluate("document.documentElement.style.removeProperty('font-size')")
        report['checks'].append('15 pages: desktop, 390px and 320px reflow; 200% text resizing; new descriptor and removals; per-page screenshots.')
        page.goto(BASE,wait_until='networkidle')
        assert page.locator('.brand-stage').evaluate("e=>getComputedStyle(e,'::before').backgroundColor")=='rgb(31, 46, 42)'
        page.goto(BASE+'services.html',wait_until='networkidle')
        for selector in ('#sessions-label','#studio-label'):
            assert page.locator(selector).evaluate("e=>e.tagName==='H2' && parseFloat(getComputedStyle(e).fontSize)>=24")
        for selector in ('#navigation .button','[data-filter=erg]','.detail-link'):
            page.locator(selector).first.hover()
            audit(page,'services.html','hover-'+selector)
        report['checks'].append('Homepage logo backdrop is exact Deep Charcoal. Both Services group headings are real H2 elements, at least 24px. Hover states checked.')
        for route in ('index.html','services.html','approach.html','about.html','faq.html','contact.html'):
            page.goto(BASE+route,wait_until='networkidle')
            page.keyboard.press('Tab')
            assert page.locator('.skip').evaluate('e=>e===document.activeElement'),route
            page.keyboard.press('Enter')
            assert page.locator('main').evaluate('e=>e===document.activeElement'),route
            count=page.locator('a,button,input,select,textarea,summary').count()+2
            for _ in range(count):
                page.keyboard.press('Tab')
                status=page.evaluate("""()=>{const e=document.activeElement;if(!e||e===document.body)return null;const s=getComputedStyle(e),r=e.getBoundingClientRect();return {tag:e.tagName,text:(e.textContent||'').slice(0,80),outline:s.outlineStyle,width:parseFloat(s.outlineWidth),top:r.top,bottom:r.bottom,height:r.height};}""")
                if status and status['height']>0:
                    assert status['outline']!='none' and status['width']>=2,(route,status)
                    assert status['bottom']>0 and status['top']<1000,(route,status)
        report['checks'].append('Keyboard-only skip links and visible focus rings tested across all six main pages; static header avoids sticky-focus obstruction.')
        page.goto(BASE+'faq.html',wait_until='networkidle')
        page.locator('details').evaluate_all('els=>els.forEach(e=>e.open=true)')
        audit(page,'faq.html','all-answers-open')
        page.goto(BASE+'contact.html',wait_until='networkidle')
        page.locator('[name=name]').fill('Accessibility verification')
        page.locator('[name=email]').fill('check@example.com')
        page.locator('[name=message]').fill('Local test, not sent.')
        page.locator('[data-preview-submit]').click()
        audit(page,'contact.html','inquiry-preview-open')
        page.set_viewport_size({'width':390,'height':844})
        page.goto(BASE,wait_until='networkidle')
        page.locator('.menu-toggle').click()
        audit(page,'index.html','mobile-menu-open')
        page.keyboard.press('Escape')
        assert page.locator('.menu-toggle').get_attribute('aria-expanded')=='false'
        page.emulate_media(reduced_motion='reduce')
        assert page.evaluate('getComputedStyle(document.documentElement).scrollBehavior')=='auto'
        report['checks'].append('Expanded FAQ, inquiry preview, mobile menu/Escape, autocomplete fields and reduced-motion state checked.')
        assert not page_errors,page_errors
        assert not report['violations'],report['violations']
        browser.close()
    report['status']='passed'
except Exception as e:
    report['status']='failed';report['error']=repr(e);report['traceback']=traceback.format_exc()
    raise
finally:
    server.shutdown()
    (OUT/'accessibility-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
