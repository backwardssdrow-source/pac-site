"""Verify the published multi-page site and approved three-section homepage."""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit
from html.parser import HTMLParser
import os, json, time, urllib.request, threading, functools
from playwright.sync_api import sync_playwright

ROOT = Path(os.environ.get('MAKEGOOD_ROOT', '.')).resolve()
SITE = ROOT / 'makegood'
M = json.loads((SITE / 'site-manifest.json').read_text())
REV = M['revision']
LOCAL = os.environ.get('MAKEGOOD_LOCAL') == '1'
REPORT = ROOT / os.environ.get('MAKEGOOD_REPORT', 'makegood-verification')
REPORT.mkdir(exist_ok=True)
MAIN_PAGES = ['index.html', 'services.html', 'approach.html', 'about.html', 'faq.html', 'contact.html']
SERVICE_PATHS = ['services.html?category=erg', 'services.html?category=presence', 'services/coaching.html']
R = {'revision': REV, 'pages': [], 'navigation': [], 'home': [], 'checks': [], 'source_files_matched': []}
server = None
if LOCAL:
    class Quiet(SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    BASE = f'http://127.0.0.1:{server.server_port}/makegood/'
else:
    BASE = 'https://backwardssdrow-source.github.io/pac-site/makegood/'
R['base'] = BASE

def fetch(path):
    with urllib.request.urlopen(BASE + path + '?release=' + REV, timeout=30) as response:
        assert response.status == 200, (path, response.status)
        return response.read()

def wait_for_release():
    deadline = time.monotonic() + 420
    while True:
        try:
            if json.loads(fetch('site-manifest.json'))['revision'] == REV:
                break
        except Exception as exc:
            print('Waiting for publication:', exc, flush=True)
        if time.monotonic() > deadline:
            raise TimeoutError(REV)
        time.sleep(10)
    def match(path):
        for _ in range(12):
            if fetch(path) == (SITE / path).read_bytes():
                return path
            time.sleep(8)
        raise AssertionError('Live bytes differ: ' + path)
    paths = M['pages'] + ['site.css', 'site-base.css', 'home.css', 'site.js', 'makegood-sunrise.svg', 'lt-founder.avif', 'travis-founder.avif']
    with ThreadPoolExecutor(max_workers=6) as pool:
        R['source_files_matched'] = list(pool.map(match, paths))

def local_fonts(page):
    if LOCAL:
        page.route('https://fonts.googleapis.com/**', lambda route: route.fulfill(status=200, content_type='text/css', body=''))

def check_home(page, engine, width, dimensions):
    assert page.locator('main > section').count() == 3
    assert page.locator('.home-paths,.home-experience,.home-approach,.context-band,main .closing,.home-proof').count() == 0
    text = page.locator('main').inner_text()
    assert '39 years' not in text and 'combined professional experience' not in text
    assert 'consulting and coaching for organizations, leaders, and individuals' in page.locator('.hero .lede').inner_text()
    assert page.locator('.home-service').count() == 3
    assert page.locator('.home-service a').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("href"))') == SERVICE_PATHS
    assert page.locator('.home-service').evaluate_all('(xs)=>xs.map(x=>x.dataset.homeAudience)') == ['erg','presence','individual']
    colors = page.locator('.home-service').evaluate_all('(xs)=>xs.map(x=>getComputedStyle(x).borderTopColor)')
    assert colors == ['rgb(240, 68, 28)', 'rgb(242, 166, 162)', 'rgb(244, 172, 12)']
    assert page.locator('.home-portraits img').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("src"))') == ['lt-founder.avif','travis-founder.avif']
    sizes = page.locator('.home-portraits img').evaluate_all('(xs)=>xs.map(x=>({w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height}))')
    assert sizes[0] == sizes[1] and sizes[0]['w'] <= 104
    assert page.locator('.home-people .home-founder-link[href="about.html#founders"]').count() == 1
    assert page.locator('.hero .home-founder-link').count() == 0
    assert page.locator('.actions .button.primary[href="services.html"]').count() == 1
    assert page.locator('.home-invitation a[href="contact.html"]').count() == 1
    assert page.locator('.hero .eyebrow').bounding_box()['y'] >= page.locator('.site-header').bounding_box()['height']
    if width <= 900:
        assert page.locator('.footer-links a:visible').count() == 1
        assert page.locator('.footer-links a:visible').get_attribute('href') == 'contact.html'
    if width <= 650:
        # Enough context for a decision, not the former full site stacked on Home.
        assert dimensions['height'] <= (2900 if width <= 360 else 2650), (engine, width, dimensions)
        size = page.locator('.hero h1').evaluate('(el)=>parseFloat(getComputedStyle(el).fontSize)')
        assert 35 <= size <= 36, size
        button = page.locator('.hero .button.primary').bounding_box()
        assert button['y'] + button['height'] <= 844, (width, button)
    R['home'].append({'browser':engine,'width':width,'height':dimensions['height'],'sections':3,'service_paths':3,'founder_photos':2})

def check_navigation(browser, engine, javascript):
    context = browser.new_context(viewport={'width': 390, 'height': 844}, java_script_enabled=javascript)
    page = context.new_page()
    local_fonts(page)
    page.goto(BASE + 'index.html?release=' + REV)
    for target in MAIN_PAGES[1:] + MAIN_PAGES[:1]:
        if javascript:
            assert page.locator('.menu-toggle').is_visible()
            assert not page.locator('#navigation').is_visible()
            page.locator('.menu-toggle').click()
            assert page.locator('.menu-toggle').get_attribute('aria-expanded') == 'true'
        else:
            assert not page.locator('.menu-toggle').is_visible()
        assert page.locator('#navigation').is_visible()
        with page.expect_navigation(wait_until='load') as navigation:
            page.locator('#navigation a[href="' + target + '"]').click()
        response = navigation.value
        assert response is not None and response.status == 200 and response.request.resource_type == 'document', target
        assert urlsplit(page.url).path.endswith('/' + target), page.url
        assert page.title() == M['expected'][target]['title']
        assert page.locator('body').get_attribute('data-page') == target
        assert page.locator('#navigation a[aria-current="page"]').count() == 1
        R['navigation'].append({'browser':engine,'javascript':javascript,'target':target,'document_response':response.status})
    if javascript:
        page.locator('.menu-toggle').click()
        page.screenshot(path=str(REPORT / (engine + '-390-menu-open.png')))
        page.keyboard.press('Escape')
        assert not page.locator('#navigation').is_visible()
        assert page.locator('.menu-toggle').get_attribute('aria-expanded') == 'false'
        page.locator('.menu-toggle').click()
        page.locator('.home-footer .footer-bottom').click()
        assert not page.locator('#navigation').is_visible()
        page.go_back()
        assert not page.locator('#navigation').is_visible()
    for target in SERVICE_PATHS + ['about.html#founders', 'contact.html']:
        page.goto(BASE + 'index.html')
        with page.expect_navigation(wait_until='load') as navigation:
            page.locator('main a[href="' + target + '"]').click()
        response = navigation.value
        assert response is not None and response.status == 200 and response.request.resource_type == 'document', target
        assert page.url == urljoin(BASE, target), page.url
        if javascript and '?category=' in target:
            category = target.split('=')[-1]
            assert page.locator('[data-filter="'+category+'"]').get_attribute('aria-pressed') == 'true'
        R['navigation'].append({'browser':engine,'javascript':javascript,'target':target,'document_response':response.status,'source':'home-overview'})
    context.close()

def verify_browser(pw, engine):
    opts = {'headless': True}
    if engine == 'chromium' and os.environ.get('CHROMIUM_PATH'):
        opts['executable_path'] = os.environ['CHROMIUM_PATH']
    browser = getattr(pw, engine).launch(**opts)
    page = browser.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    local_fonts(page)
    axe = ROOT / 'node_modules/axe-core/axe.min.js'
    widths = [1440, 1024, 900, 768, 430, 390, 375, 320] if engine == 'chromium' else [390, 320]
    for width in widths:
        page.set_viewport_size({'width':width,'height':1000 if width > 900 else 844})
        for route in M['pages']:
            response = page.goto(BASE + route + '?release=' + REV, wait_until='load')
            assert response.status == 200, route
            page.evaluate('document.fonts.ready')
            assert page.locator('h1').count() == 1 and page.title() == M['expected'][route]['title'], route
            assert page.locator('meta[name="site-revision"]').get_attribute('content') == M['expected'][route].get('revision', REV), route
            assert page.locator('meta[name="robots"]').get_attribute('content') == 'noindex,nofollow', route
            assert page.locator('.footer-links a').count() == 6, route
            for image in page.locator('img').all():
                if image.is_visible():
                    image.scroll_into_view_if_needed()
                image.evaluate('(image)=>image.decode()')
            page.evaluate('scrollTo(0,0)')
            assert page.locator('img').evaluate_all('(images)=>images.every(image=>image.complete&&image.naturalWidth>0)'), route
            dim = page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight})')
            assert dim['scroll'] <= width + 1, (engine, route, width, dim)
            assert page.locator('body').evaluate('(el)=>getComputedStyle(el).fontSize') == '18px', route
            h = M['expected'][route]['background_hex'].lstrip('#')
            wanted = 'rgb(' + ', '.join(str(int(h[i:i+2],16)) for i in (0,2,4)) + ')'
            assert page.locator('main').evaluate('(el)=>getComputedStyle(el).backgroundColor') == wanted, route
            controls = page.locator('.footer-links a:visible').evaluate_all('(xs)=>xs.map(x=>({size:getComputedStyle(x).fontSize,h:x.getBoundingClientRect().height}))')
            assert all(x['size']=='16px' and x['h']>=44 for x in controls), (route, controls)
            if width <= 900:
                assert not page.locator('#navigation').is_visible() and page.locator('.menu-toggle').is_visible(), route
                assert page.locator('.site-header').bounding_box()['height'] <= 84, route
                assert page.locator('.menu-toggle').bounding_box()['height'] >= 44, route
            if route == 'index.html':
                check_home(page, engine, width, dim)
            if route == 'about.html':
                assert page.locator('.founder-portrait img').evaluate_all('(xs)=>xs.map(x=>x.getAttribute("src"))') == ['lt-founder.avif','travis-founder.avif']
                assert page.locator('#experience .experience-item').count() == 4
                assert '39 years of combined professional experience' in page.locator('#founders').inner_text()
            if route == 'approach.html':
                assert page.locator('#why-now-heading').count() == 1
            violations = []
            ran = False
            if axe.exists() and width in [1440,390] and engine == 'chromium':
                page.add_script_tag(path=str(axe))
                result = page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}})")
                violations = [{'id':v['id'],'impact':v['impact'],'nodes':[n['target'] for n in v['nodes']]} for v in result['violations']]
                ran = True
                assert not violations, (route, width, violations)
            R['pages'].append({'browser':engine,'route':route,'width':width,'height':dim['height'],'overflow':False,'automated_accessibility_run':ran,'violations':violations})
            if route in ['index.html','about.html','services.html'] and width in [1440,390,320]:
                page.screenshot(path=str(REPORT / f'{engine}-{width}-{route}.png'), full_page=True)
        print('Checked',len(M['pages']),'pages:',engine,width,flush=True)
    check_navigation(browser, engine, True)
    check_navigation(browser, engine, False)
    page.goto(BASE + 'services.html?category=erg')
    for category, count in [('erg',5),('presence',4),('individual',1),('all',9)]:
        page.locator(f'[data-filter="{category}"]').click()
        assert page.locator('.offer:not([hidden])').count() == count
    page.goto(BASE + 'services/senior-presence-advisory.html')
    page.locator('.detail-summary .button').click()
    assert page.locator('#service-select').input_value() == 'senior-presence-advisory'
    sent = []
    page.on('request',lambda request:sent.append(request.url) if request.method not in ['GET','HEAD'] else None)
    page.locator('input[name=name]').fill('Review check')
    page.locator('input[name=email]').fill('test@example.com')
    page.locator('textarea').fill('Non-sending review check')
    page.locator('[data-preview-submit]').click()
    assert 'NOT SENT' in page.locator('#inquiry-text').inner_text() and not sent
    page.goto(BASE + 'faq.html#terms')
    assert page.locator('#terms').get_attribute('open') is not None
    page.goto(BASE + 'index.html#experience')
    page.wait_for_url('**/about.html#experience')
    for route in ['index.html','services.html','approach.html','services/senior-presence-advisory.html']:
        page.goto(BASE + route)
        page.add_style_tag(content='*{line-height:1.5!important;letter-spacing:.12em!important;word-spacing:.16em!important}p{margin-bottom:2em!important}')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'), route
    context = browser.new_context(java_script_enabled=False)
    nojs = context.new_page()
    local_fonts(nojs)
    nojs.goto(BASE+'contact.html')
    assert nojs.locator('[data-preview-submit]').is_disabled() and nojs.locator('input[name=email]').is_disabled()
    context.close()
    assert not errors, errors
    browser.close()

try:
    if not LOCAL:
        wait_for_release()
    for route in M['pages']:
        class Links(HTMLParser):
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == 'a' and 'href' in attrs:
                    url = urlsplit(urljoin(BASE + route, attrs['href']))
                    if url.netloc == urlsplit(BASE).netloc and url.path.startswith(urlsplit(BASE).path):
                        target = url.path[len(urlsplit(BASE).path):] or 'index.html'
                        assert target in M['pages'], (route, attrs['href'])
                        if url.fragment:
                            assert 'id="'+url.fragment+'"' in (SITE/target).read_text(), (route, attrs['href'])
        Links().feed((SITE/route).read_text())
    with sync_playwright() as pw:
        verify_browser(pw, 'chromium')
        if os.environ.get('MAKEGOOD_WEBKIT') == '1':
            verify_browser(pw, 'webkit')
    R['checks'] = ['Three-section Home: introduction, service summaries, brief founder context; no tenure statistic', 'All five homepage overview links and all six menu destinations load independent documents with and without JavaScript', 'Menu closes on Escape, outside click and back navigation', 'Both founder portraits unchanged, equal-sized, and loading', 'Service filters, non-sending contact draft, FAQ anchors and legacy experience link', 'Every internal path and anchor resolves', 'No horizontal overflow at tested sizes; custom text spacing checked']
    R['status'] = 'passed'
    print('PASSED', REV, flush=True)
except Exception as exc:
    R['status'] = 'failed'
    R['error'] = repr(exc)
    raise
finally:
    (REPORT/'report.json').write_text(json.dumps(R,indent=2))
    if server:
        server.shutdown()
