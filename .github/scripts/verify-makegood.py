from pathlib import Path
import json, re, time, traceback, urllib.request
from playwright.sync_api import sync_playwright

BASE = 'https://backwardssdrow-source.github.io/pac-site/makegood/'
OLD = 'https://backwardssdrow-source.github.io/pac-site/in-good-company-preview/'
OUT = Path('makegood-verification')
OUT.mkdir(exist_ok=True)
report = {'url': BASE, 'checks': [], 'errors': []}
expected = {'coaching': 'Fee confirmed before booking', 'decision-session': '$1,250', 'practice-lab': '$2,500', 'erg-portfolio-diagnostic': '$9,000', 'erg-operating-model-build': '$18,000', 'fractional-erg-office': '$7,500', 'presence-scan': '$5,000', 'presence-lab': '$10,000', 'senior-presence-advisory': '$2,000'}
removed_positioning = re.compile(r'remote[\s\-\u2010-\u2014]*first', re.I)
names = ('index.html', 'sunrise.css', 'sunrise.js', 'brand-update.css', 'makegood-sunrise.svg')
source_files = {name: (Path('makegood') / name).read_bytes() for name in names}
for name, data in source_files.items():
    (OUT / name).write_bytes(data)

def contrast(first, second):
    def luminance(value):
        values = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    lo, hi = sorted((luminance(first), luminance(second)))
    return (hi + .05) / (lo + .05)

try:
    for name, data in source_files.items():
        assert not removed_positioning.search(data.decode()), f'Obsolete positioning in {name}'
    for attempt in range(40):
        try:
            published = {name: urllib.request.urlopen(BASE + name + '?verify=' + str(time.time_ns()), timeout=20).read() for name in source_files}
            if all(published[name] == data for name, data in source_files.items()):
                break
        except Exception:
            pass
        time.sleep(10)
    else:
        raise RuntimeError('Published MakeGood assets did not match the current commit within the verification window.')
    report['checks'].append('All five published assets match committed source')
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        response = page.goto(BASE, wait_until='networkidle')
        assert response.status == 200
        assert not removed_positioning.search(page.content())
        assert page.title() == 'MakeGood Co. | Services and Founding Pricing'
        assert page.locator('link[rel=canonical]').get_attribute('href') == BASE
        assert '$250' not in page.locator('body').inner_text()
        assert page.locator('.brand img').evaluate('(el) => el.complete && el.naturalWidth > 0')
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 1')
        refreshed = page.locator('meta[name="brand-revision"]').count() > 0
        if refreshed:
            palette = {'--evergreen': '#183F35', '--mulberry': '#4A213A', '--clay': '#974B36', '--sage': '#D7DDCB'}
            for token, value in palette.items():
                actual = page.evaluate('(name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()', token)
                assert actual.lower() == value.lower(), token
            pairs = [('#183F35', '#F7EDDF'), ('#4A213A', '#F7EDDF'), ('#974B36', '#F7EDDF'), ('#252820', '#D7DDCB')]
            report['contrast_pairs'] = [{'colors': pair, 'ratio': round(contrast(*pair), 2)} for pair in pairs]
            assert all(contrast(*pair) >= 4.5 for pair in pairs)
            assert not re.search(r'[↗→↓]', page.locator('body').inner_text())
            # innerText includes text-transform: uppercase; the words/order must still match.
            descriptor = page.locator('.brandtext').inner_text()
            assert descriptor.casefold().split() == ['people.', 'culture.', 'practice.'], repr(descriptor)
            assert page.locator('.button.primary').first.evaluate('(el) => getComputedStyle(el).backgroundColor') == 'rgb(24, 63, 53)'
            report['checks'].append('Approved accent values and four AA text pairs; consistent descriptor; no decorative arrows')
        page.screenshot(path=str(OUT / 'desktop-top.png'))
        page.screenshot(path=str(OUT / 'desktop-full.png'), full_page=True)
        report['checks'].append('Published route, original logo, canonical address, title and founding pricing')
        for service, fee in expected.items():
            page.goto(BASE + '#service-' + service, wait_until='networkidle')
            page.locator('#service-modal[open]').wait_for()
            detail_text = page.locator('#service-body').inner_text()
            assert fee in detail_text, service
            assert not removed_positioning.search(detail_text), service
            if refreshed:
                assert not re.search(r'[↗→↓]', detail_text), service
            page.keyboard.press('Escape')
            assert not page.locator('#service-modal').evaluate('(el) => el.open')
        report['checks'].append('All nine detail routes, preserved fees and Escape closing')
        page.goto(BASE + '#services', wait_until='networkidle')
        page.locator('[data-filter=individual]').click()
        assert page.locator('.studio-grid').is_hidden()
        assert page.locator('#service-coaching').is_visible()
        page.locator('[data-filter=all]').click()
        assert page.locator('.studio-grid').is_visible()
        report['checks'].append('Service filters')
        page.goto(BASE + '#contact', wait_until='networkidle')
        page.locator('[name=name]').fill('Website verification')
        page.locator('[name=email]').fill('check@example.com')
        page.locator('[name=message]').fill('Local inquiry-preview test. Do not send.')
        page.locator('#inquiry-form button[type=submit]').click()
        assert page.locator('#inquiry-modal').evaluate('(el) => el.open')
        assert 'not sent' in page.locator('#inquiry-text').inner_text().lower()
        page.keyboard.press('Escape')
        report['checks'].append('Inquiry is explicitly an unsent local preview; no booking or payment created')
        for width in (390, 320):
            page.set_viewport_size({'width': width, 'height': 844})
            page.goto(BASE, wait_until='networkidle')
            assert not removed_positioning.search(page.content())
            assert not page.evaluate('document.documentElement.scrollWidth > innerWidth + 1'), f'Horizontal overflow at {width}'
            page.screenshot(path=str(OUT / f'mobile-{width}-top.png'))
            page.locator('.menu-toggle').click()
            assert page.locator('.menu-toggle').get_attribute('aria-expanded') == 'true'
            page.keyboard.press('Escape')
            page.goto(BASE + '#service-decision-session', wait_until='networkidle')
            assert page.locator('#service-modal').evaluate('(el) => el.open')
            assert not removed_positioning.search(page.locator('#service-body').inner_text())
            page.screenshot(path=str(OUT / f'mobile-{width}-details.png'))
        report['checks'].append('Mobile layouts and menus at 390px and 320px')
        page.goto(OLD + '?ref=migration-check#/service/presence-scan', wait_until='networkidle')
        page.wait_for_url('**/makegood/**')
        assert '/pac-site/makegood/' in page.url
        assert 'ref=migration-check' in page.url
        assert 'Presence Scan' in page.locator('#service-body').inner_text()
        report['checks'].append('Legacy address redirects with query and service hash preserved')
        assert not errors, errors
        browser.close()
    report['status'] = 'passed'
except Exception as error:
    report['status'] = 'failed'
    report['errors'].append(repr(error))
    report['traceback'] = traceback.format_exc()
    raise
finally:
    (OUT / 'report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
