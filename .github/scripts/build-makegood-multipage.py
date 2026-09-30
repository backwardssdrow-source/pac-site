"""Build standalone MakeGood pages from the approved copy snapshot.
Run from repository root: python .github/scripts/build-makegood-multipage.py
The snapshot preserves all service fees, scopes and terms.
Founder-approved mission/vision in makegood-approved-messaging.json override
older purpose/vision language in the original migration snapshot.
"""
from pathlib import Path
from copy import deepcopy
import html
import json
from bs4 import BeautifulSoup

ROOT = Path('makegood')
SOURCE = BeautifulSoup(Path('.github/makegood-source.html').read_text(), 'html.parser')
APPROVED = json.loads(Path('.github/makegood-approved-messaging.json').read_text(encoding='utf-8'))
purpose = SOURCE.select_one('#about .purpose')
if purpose is None:
    raise ValueError('About-page mission/vision container is missing.')
purpose.clear()
for label, key in (('Our mission', 'mission'), ('Our vision', 'vision')):
    value = APPROVED.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'Approved {key} must be a nonempty string.')
    heading = SOURCE.new_tag('h3')
    heading.string = label
    paragraph = SOURCE.new_tag('p')
    paragraph.string = value
    purpose.extend([heading, paragraph])
SERVICES = json.loads(SOURCE.select_one('#services-data').string)
BASE = 'https://backwardssdrow-source.github.io/pac-site/makegood/'
REV = '20260930-multipage-1'
NAV = [('home', 'Home', 'index.html'), ('services', 'Services', 'services.html'), ('approach', 'Our approach', 'approach.html'), ('about', 'About', 'about.html'), ('faq', 'FAQs', 'faq.html'), ('contact', 'Contact', 'contact.html')]
ROUTES = {key: path for key, _, path in NAV}
ROUTES['terms'] = 'faq.html#terms'
ROUTES.update({'service-' + s['id']: 'services/' + s['id'] + '.html' for s in SERVICES})
esc = html.escape

def fragment(value):
    return BeautifulSoup(value, 'html.parser')

def nav_markup(active, prefix, detail=False):
    links = []
    for key, label, path in NAV:
        state = ''
        if key == active:
            state = ' aria-current="' + ('location' if detail else 'page') + '"'
        css = ' class="button dark"' if key == 'contact' else ''
        links.append(f'<a href="{prefix}{path}"{css}{state}>{label}</a>')
    return ''.join(links)

def rebase(node, prefix):
    for badge in node.select('.stage-note, .arrow'):
        badge.decompose()
    for element in node.select('[data-route]'):
        del element['data-route']
    for anchor in node.select('a[href]'):
        value = anchor['href']
        if value.startswith('#') and value[1:] in ROUTES:
            anchor['href'] = prefix + ROUTES[value[1:]]
    for image in node.select('img[src]'):
        if image['src'] == 'makegood-sunrise.svg':
            image['src'] = prefix + image['src']
    return str(node)

def breadcrumb(label, prefix='', service=False):
    middle = f'<a href="{prefix}services.html">Services</a><span aria-hidden="true">/</span>' if service else ''
    return f'<nav class="breadcrumbs wrap" aria-label="Breadcrumb"><a href="{prefix}index.html">Home</a><span aria-hidden="true">/</span>{middle}<span aria-current="page">{esc(label)}</span></nav>'

def render(path, title, description, content, active, detail=False):
    prefix = '../' if detail else ''
    header = deepcopy(SOURCE.select_one('header.nav'))
    header.select_one('.navlinks').clear()
    header.select_one('.navlinks').append(fragment(nav_markup(active, prefix, detail)))
    footer = deepcopy(SOURCE.select_one('footer.footer'))
    footer.select_one('.footer-links').clear()
    footer.select_one('.footer-links').append(fragment(''.join(f'<a href="{prefix}{target}">{label}</a>' for _, label, target in NAV)))
    canonical = BASE + ('' if path == 'index.html' else path)
    banner = str(SOURCE.select_one('.previewbar'))
    page_class = 'detail' if detail else active
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><meta name="description" content="{esc(description, quote=True)}"><meta name="theme-color" content="#F7EDDF"><meta name="brand-revision" content="sunrise-accents-2026-09-30"><meta name="site-revision" content="{REV}"><title>{esc(title)} | MakeGood Co.</title><link rel="canonical" href="{canonical}"><link rel="stylesheet" href="{prefix}sunrise.css"><link rel="stylesheet" href="{prefix}brand-update.css?v={REV}"><link rel="stylesheet" href="{prefix}pages.css?v={REV}"><script>document.documentElement.classList.add('js');</script><script src="{prefix}pages.js?v={REV}" defer></script></head>
<body class="multipage page-{page_class}" data-page="{active}" data-root="{prefix}"><a class="skip" href="#main">Skip to content</a>{banner}{rebase(header, prefix)}<main id="main" tabindex="-1">{content}</main>{rebase(footer, prefix)}</body></html>'''
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(document, encoding='utf-8')

# Home: a focused introduction, not a duplicate of every section.
hero = deepcopy(SOURCE.select_one('#home'))
hero.select_one('.stage-note').decompose()
hero.select_one('.hero-bottom').decompose()
teasers = '''<section class="home-paths"><div class="wrap"><div class="home-paths-head"><h2>Three ways to work with us.</h2><p>Choose the support that fits what you are working through.</p></div><div class="path-grid"><article class="path-card"><p class="eyebrow">For individuals</p><h3>Coaching</h3><p>Space to think through work, leadership, communication and change.</p><a class="text-link" href="services.html?category=individual">Explore coaching</a></article><article class="path-card"><p class="eyebrow">For employee resource groups</p><h3>ERG Studio</h3><p>Practical support for ERG strategy, governance, sponsorship and operations.</p><a class="text-link" href="services.html?category=erg">Explore ERG services</a></article><article class="path-card"><p class="eyebrow">For leaders and teams</p><h3>Presence Studio</h3><p>Understand the experience you create and strengthen how you work with others.</p><a class="text-link" href="services.html?category=presence">Explore leadership services</a></article></div></div></section>'''
render('index.html', 'Better ways of working. Built with people.', 'Coaching, ERG advisory and leadership development. MakeGood Co. helps people and organizations turn intention into practice.', rebase(hero, '') + teasers, 'home')

meta = {
    'services': ('Services and founding fees', 'Explore coaching, focused sessions, ERG advisory and leadership development, with clear scopes and founding fees.'),
    'approach': ('Our approach', 'Listen carefully, make sense of the system, and build practical tools and agreements people can use.'),
    'about': ('About MakeGood Co.', 'An independent company founded by LT and Travis, bringing coaching, ERG advisory and leadership development together.'),
    'faq': ('Frequently asked questions', 'Answers about scope, fees, delivery, confidentiality, payment terms and starting work with MakeGood Co.'),
    'contact': ('Start a conversation', 'Tell us what you are working through. The inquiry form is an unsent local preview; booking and payments are not connected.')
}
for key, (title, description) in meta.items():
    section = deepcopy(SOURCE.select_one('#' + key))
    heading = section.find('h2')
    assert heading is not None, key
    heading.name = 'h1'
    for number in section.select('.eyebrow .number'):
        number.decompose()
    if key == 'services':
        heading.clear()
        heading.append('Find the right support.')
        filters = section.select_one('.service-filters')
        filters['role'] = 'group'
        status = fragment('<p class="filter-status" id="filter-status" role="status" aria-live="polite"></p>')
        filters.insert_after(status)
    if key == 'contact':
        button = section.select_one('button[type=submit]')
        button['disabled'] = ''
        button['data-preview-submit'] = ''
        note = fragment('<noscript><p>This local preview requires JavaScript. No information can be submitted from this form.</p></noscript>')
        section.select_one('form').append(note)
        preview = fragment('''<section class="inquiry-result" id="inquiry-preview-panel" hidden tabindex="-1" aria-labelledby="inquiry-title"><p class="eyebrow">Inquiry preview · Not sent</p><h2 id="inquiry-title">Your draft inquiry</h2><p>Nothing has been sent or saved by this site. You can copy the draft or save a text file on your device.</p><pre class="inquiry-preview" id="inquiry-text"></pre><div class="actions"><button class="button dark" id="copy-inquiry" type="button">Copy inquiry</button><button class="button" id="save-inquiry" type="button">Save as text</button><button class="button" id="edit-inquiry" type="button">Edit inquiry</button></div><p class="status" id="copy-status" role="status" aria-live="polite"></p></section>''')
        section.select_one('.contact-grid').append(preview)
    render(key + '.html', title, description, breadcrumb(NAV[[x[0] for x in NAV].index(key)][1]) + rebase(section, ''), key)

# Actual service pages: all scope and fee text is copied verbatim from approved data.
for service in SERVICES:
    identifier = service['id']
    title = service['name']
    items = ''.join('<li>' + esc(item) + '</li>' for item in service['items'])
    suffix = '<span class="fee-suffix">' + esc(service['suffix']) + '</span>' if service.get('suffix') else ''
    fee_class = ' fee-confirm' if identifier == 'coaching' else ''
    content = breadcrumb(title, '../', True) + f'''<section class="service-detail section"><div class="wrap detail-grid"><article class="detail-copy"><p class="eyebrow">{esc(service['practice'])}</p><h1>{esc(title)}</h1><p class="detail-intro">{esc(service['intro'])}</p><p>{esc(service['details'])}</p><h2>What is included</h2><ul class="scope-list">{items}</ul><section class="scope-boundary"><h2>Scope and boundaries</h2><p>{esc(service['boundary'])}</p></section></article><aside class="detail-summary" aria-label="Fee and next steps"><p class="eyebrow">Founding fee · USD</p><p class="detail-fee{fee_class}">{esc(service['fee'])}{suffix}</p><p class="detail-duration">{esc(service['duration'])}</p><a class="button primary" href="../contact.html?service={identifier}">Start a conversation</a><p class="detail-note">Scope, fee and timing are confirmed in writing before work begins. Booking and payments are not connected to this preview.</p><a class="text-link" href="../faq.html#terms">Read fees and terms</a><a class="text-link" href="../services.html">View all services</a></aside></div></section>'''
    render('services/' + identifier + '.html', title, service['intro'], content, 'services', True)

manifest = {'revision': REV, 'pages': [target for _, _, target in NAV] + ['services/' + s['id'] + '.html' for s in SERVICES], 'service_count': len(SERVICES), 'original_logo_unchanged': True}
(ROOT / 'site-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
(ROOT / 'README.md').write_text('''# MakeGood Co. standalone website

The site has six main pages and nine service-detail pages. Navigation uses real HTML URLs; JavaScript only enhances menus, filters, legacy redirects and the explicitly unsent inquiry preview.

The approved Sunrise logo, palette, pricing and service scopes are preserved. The circular hero badge is removed from the markup.

## Sources
- `.github/makegood-approved-messaging.json`: exact mission and vision approved by LT and Travis. This overrides the older purpose/vision copy in the migration snapshot.
- `.github/makegood-source.html`: content snapshot before the multipage migration; source for service descriptions, fees, scopes and terms.
- `.github/scripts/build-makegood-multipage.py`: deterministic page builder (requires BeautifulSoup4).
- `sunrise.css` and `brand-update.css`: existing design and approved color extension.
- `pages.css` and `pages.js`: multipage layout and progressive enhancements.

Keep mission and vision verbatim. Service descriptions and the People. Culture. Practice. descriptor are supporting copy, not replacement mission/vision statements. Edit the approved messaging file, snapshot or builder as appropriate, then regenerate. Do not restore single-page navigation or load `sunrise.js` on these pages.

## Preview limitations
The inquiry preview sends nothing, stores nothing, and makes no booking or charge. A user may explicitly copy the draft or save a text file to their own device.
''')
print(json.dumps(manifest, indent=2))
