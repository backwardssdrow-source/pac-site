"""Verify local build (MAKEGOOD_LOCAL=1) or the deployed MakeGood site."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, os, re, threading, time, traceback, urllib.request
from playwright.sync_api import sync_playwright

OUT = Path('makegood-verification')
OUT.mkdir(exist_ok=True)
LOCAL = os.environ.get('MAKEGOOD_LOCAL') == '1'
server = None
if LOCAL:
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *args): pass
    server = ThreadingHTTPServer(('127.0.0.1', 8765), partial(QuietHandler, directory=str(Path.cwd())))
    threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:8765/makegood/' if LOCAL else 'https://backwardssdrow-source.github.io/pac-site/makegood/'
OLD = BASE.replace('makegood/', 'in-good-company-preview/')
manifest = json.loads(Path('makegood/site-manifest.json').read_text())
source = Path('.github/makegood-source.html').read_text()
services = json.loads(re.search(r'<script id="services-data" type="application/json">(.*?)</script>', source, re.S).group(1))
report = {'url': BASE, 'revision': manifest['revision'], 'checks': [], 'errors': []}

def contrast(a, b):
    def lum(color):
        vals = [int(color[i:i+2], 16)/255 for i in (1,3,5)]
        vals = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in vals]
        return sum(v*w for v,w in zip(vals,(.2126,.7152,.0722)))
    low, high = sorted((lum(a), lum(b)))
    return (high+.05)/(low+.05)

try:
    assert manifest['service_count'] == 9 and len(manifest['pages']) == 15
    if not LOCAL:
        names = manifest['pages'] + ['pages.css','pages.js','brand-update.css','makegood-sunrise.svg']
        expected = {name: (Path('makegood')/name).read_bytes() for name in names}
        def matches(name):
            request = urllib.request.Request(BASE + name + '?check=' + str(time.time_ns()), headers={'Cache-Control':'no-cache'})
            return urllib.request.urlopen(request, timeout=20).read() == expected[name]
        for attempt in range(30):
            try:
                with ThreadPoolExecutor(max_workers=8) as pool:
                    if all(pool.map(matches, names)): break
            except Exception: pass
            time.sleep(8)
        else: raise RuntimeError('Published pages did not match the tested source within the deployment window.')
        report['checks'].append('All 15 published pages and shared assets match committed source')
    logo = Path('makegood/makegood-sunrise.svg').read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(logo)).encode() + b'\0' + logo).hexdigest()
    assert blob == '0b2144e837f84791e467ce0ed8b71c8fd58335b7', 'Original logo changed'
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width':1440,'height':1000})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        for route in manifest['pages']:
            response = page.goto(BASE + route, wait_until='networkidle')
            assert response.status == 200, route
            assert page.locator('main h1').count() == 1, route
            assert page.locator('nav[aria-label="Main navigation"] a').count() == 6, route
            assert page.locator('nav[aria-label="Main navigation"] a[href^="#"]').count() == 0, route
            assert page.locator('.stage-note').count() == 0, route
            assert page.locator('#service-modal').count() == 0, route
            assert page.locator('script[src*="sunrise.js"]').count() == 0, route
            assert page.locator('meta[name=site-revision]').get_attribute('content') == manifest['revision']
            assert page.locator('.brand img').evaluate('(el) => el.complete && el.naturalWidth > 0'), route
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 1'), route
            assert not re.search(r'[↗→↓]', page.locator('body').inner_text()), route
            for width in (390, 320):
                page.set_viewport_size({'width':width,'height':844})
                assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 1'), (route,width)
            page.set_viewport_size({'width':1440,'height':1000})
        report['checks'].append('15 standalone pages: one H1, six real navigation URLs, loaded logo, no badge or service modal, no horizontal overflow at 1440/390/320px')
        for service in services:
            page.goto(BASE + 'services/' + service['id'] + '.html', wait_until='networkidle')
            body = page.locator('main').inner_text()
            assert page.locator('h1').inner_text() == service['name']
            for text in [service['fee'], service['duration'], service['intro'], service['details'], service['boundary']] + service['items']:
                assert text in body, (service['id'], text)
            page.locator('.detail-summary .button').click()
            page.wait_for_url('**/contact.html?service=' + service['id'])
            assert page.locator('#service-select').input_value() == service['id']
        report['checks'].append('All nine service pages preserve every fee, duration, scope item and boundary; inquiry selection carries over')
        page.goto(BASE, wait_until='networkidle')
        for route in ('services.html','approach.html','about.html','faq.html','contact.html','index.html'):
            page.locator('#navigation a[href="' + route + '"]').click()
            page.wait_for_url('**/' + route)
            assert page.locator('#navigation a[aria-current=page]').count() == 1
        page.go_back(wait_until='networkidle')
        assert '/contact.html' in page.url
        report['checks'].append('Main navigation opens distinct documents; current-page state and browser Back work')
        page.goto(BASE + 'services.html', wait_until='networkidle')
        page.locator('[data-filter=individual]').click()
        assert page.locator('.studio-grid').is_hidden()
        assert page.locator('#service-coaching').is_visible()
        assert '1 service' in page.locator('#filter-status').inner_text()
        page.locator('[data-filter=erg]').click()
        assert page.locator('.studio-panel.erg').is_visible()
        assert page.locator('.studio-panel.presence').is_hidden()
        page.locator('[data-filter=all]').click()
        page.locator('#service-decision-session a').click()
        page.wait_for_url('**/services/decision-session.html')
        report['checks'].append('Service directory filters and standalone detail links work')
        page.goto(BASE + 'contact.html', wait_until='networkidle')
        requests = []
        page.on('request', lambda request: requests.append(request.url))
        page.locator('[name=name]').fill('Website verification')
        page.locator('[name=email]').fill('check@example.com')
        page.locator('[name=message]').fill('<script>test</script> — local draft only')
        before = len(requests)
        page.locator('#inquiry-form button[type=submit]').click()
        assert page.locator('#inquiry-preview-panel').is_visible()
        assert 'NOT SENT' in page.locator('#inquiry-text').inner_text()
        assert '<script>test</script>' in page.locator('#inquiry-text').inner_text()
        assert page.locator('#inquiry-text script').count() == 0
        assert len(requests) == before, 'Form issued a network request'
        with page.expect_download() as info:
            page.locator('#save-inquiry').click()
        assert info.value.suggested_filename == 'MakeGood-inquiry-draft.txt'
        page.locator('#edit-inquiry').click()
        assert page.locator('#inquiry-preview-panel').is_hidden()
        report['checks'].append('Inquiry is an inline unsent preview; safe text output, no network submission, explicit file save and edit work')
        for width in (390,320):
            page.set_viewport_size({'width':width,'height':844})
            page.goto(BASE, wait_until='networkidle')
            page.locator('.menu-toggle').click()
            assert page.locator('.menu-toggle').get_attribute('aria-expanded') == 'true'
            page.keyboard.press('Escape')
            assert page.locator('.menu-toggle').get_attribute('aria-expanded') == 'false'
            page.locator('.menu-toggle').click()
            page.locator('#navigation a[href="about.html"]').click()
            page.wait_for_url('**/about.html')
            page.goto(BASE, wait_until='networkidle')
            page.screenshot(path=str(OUT/f'home-mobile-{width}.png'), full_page=True)
        page.set_viewport_size({'width':1440,'height':1000})
        page.goto(BASE, wait_until='networkidle')
        pairs = [('#183F35','#F7EDDF'),('#4A213A','#F7EDDF'),('#974B36','#F7EDDF'),('#252820','#D7DDCB')]
        report['contrast_pairs'] = [{'colors': pair, 'ratio': round(contrast(*pair),2)} for pair in pairs]
        assert all(contrast(*pair) >= 4.5 for pair in pairs)
        for token, value in {'--evergreen':'#183F35','--mulberry':'#4A213A','--clay':'#974B36','--sage':'#D7DDCB'}.items():
            assert page.evaluate('(name)=>getComputedStyle(document.documentElement).getPropertyValue(name).trim().toLowerCase()', token) == value.lower()
        page.screenshot(path=str(OUT/'home-desktop.png'), full_page=True)
        page.goto(BASE+'services.html', wait_until='networkidle')
        page.screenshot(path=str(OUT/'services-desktop.png'), full_page=True)
        page.goto(BASE+'services/erg-portfolio-diagnostic.html', wait_until='networkidle')
        page.screenshot(path=str(OUT/'service-detail-desktop.png'), full_page=True)
        report['checks'].append('Mobile menus, Escape behavior, original SVG and four approved accent contrast pairs')
        page.goto(BASE+'#about', wait_until='networkidle')
        page.wait_for_url('**/about.html')
        page.goto(BASE+'#service-presence-scan', wait_until='networkidle')
        page.wait_for_url('**/services/presence-scan.html')
        page.goto(OLD+'?ref=migration-check#/service/presence-scan', wait_until='networkidle')
        page.wait_for_url('**/services/presence-scan.html?ref=migration-check')
        page.goto(BASE+'faq.html#terms', wait_until='networkidle')
        assert page.locator('#terms').evaluate('(el)=>el.open')
        report['checks'].append('Old section links, service links and legacy website redirect resolve to new pages; terms open directly')
        context = browser.new_context(java_script_enabled=False, viewport={'width':390,'height':844})
        nojs = context.new_page()
        nojs.goto(BASE+'services.html')
        assert nojs.locator('#navigation a[href="about.html"]').is_visible()
        nojs.locator('#service-decision-session a').click()
        nojs.wait_for_url('**/services/decision-session.html')
        nojs.goto(BASE+'contact.html')
        assert nojs.locator('[data-preview-submit]').is_disabled()
        context.close()
        report['checks'].append('Navigation and service pages work without JavaScript; nonfunctional preview submit stays disabled')
        assert not errors, errors
        browser.close()
    report['status'] = 'passed'
except Exception as error:
    report['status'] = 'failed'
    report['errors'].append(repr(error))
    report['traceback'] = traceback.format_exc()
    raise
finally:
    if server: server.shutdown()
    (OUT/'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
