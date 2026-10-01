"""Apply LT's 1 October 2026 visual/copy revisions without changing fees or scope.
Idempotent source migration; run from the repository root before the page builder.
"""
from pathlib import Path
import json, re
from bs4 import BeautifulSoup

REV = '20261001-palette14-a11y'
ROOT = Path('makegood')
PALETTE = {'orange':'#F0441C','blush':'#F2A6A2','gold':'#F4AC0C','olive':'#697A39','teal':'#2E7D7A','indigo':'#2E3A8C','lilac':'#C9B4DA','terracotta':'#C65A3A','charcoal':'#1F2E2A','cream':'#FAF7F2'}
# Remove every obsolete literal, including translucent old-color shadows/borders.
COLORS = {'#f7eddf':'#FAF7F2','#252820':'#1F2E2A','#fffcf7':'#FAF7F2','#626457':'#1F2E2A','#dcd4c6':'#C9B4DA','#f4e4cf':'#FAF7F2','#f8d17b':'#F4AC0C','#414537':'#1F2E2A','#25282032':'#C9B4DA','#f4d8ca':'#F2A6A2','#e5e7d6':'#C9B4DA','#f0f0e6':'#C9B4DA','#dadbca':'#FAF7F2','#f7eddf44':'#C9B4DA','#d5d5c6':'#FAF7F2','#25282022':'#C9B4DA','#25282025':'#1F2E2A','#f0e5d5':'#FAF7F2','#b5b49f':'#C9B4DA','#25282060':'#1F2E2A','#25282015':'#C9B4DA','#b8b6a6':'#1F2E2A','#78796c':'#1F2E2A','#f7eddf33':'#C9B4DA','#cfcebc':'#FAF7F2','#0005':'#1F2E2A','#252820af':'#1F2E2A','#eee3d1':'#C9B4DA','#183f35':'#1F2E2A','#4a213a':'#2E3A8C','#974b36':'#C65A3A','#d7ddcb':'#C9B4DA'}
for path in ROOT.glob('*.css'):
    text = path.read_text()
    text = re.sub(r'#[0-9a-fA-F]{3,8}\b', lambda m: COLORS.get(m.group().lower(), m.group()), text)
    for old, new in {'--evergreen':'--charcoal','--mulberry':'--indigo','--clay':'--terracotta','--sage':'--lilac'}.items():
        text = text.replace(old,new)
    if path.name == 'brand-update.css':
        text = re.sub(r'^/\*.*?\*/', '/* Layout layer, migrated to the corrected v1.4 palette. Page-specific color roles are in palette.css. */', text, count=1, flags=re.S)
    # Let text-only browser resizing work for legacy fixed-size labels too.
    text = re.sub(r'font-size:\s*(\d+(?:\.\d+)?)px', lambda m: 'font-size:' + format(float(m.group(1))/16,'.6g') + 'rem', text)
    path.write_text(text)
    actual = {x.upper() for x in re.findall(r'#[0-9a-fA-F]{3,8}\b',text)}
    assert actual <= set(PALETTE.values()), (str(path),actual-set(PALETTE.values()))

approved_path = Path('.github/makegood-approved-messaging.json')
approved = json.loads(approved_path.read_text())
approved['descriptor'] = 'People. Culture. Possibilities.'
approved['descriptor_approved'] = '2026-10-01'
approved_path.write_text(json.dumps(approved,ensure_ascii=False,indent=2)+'\n')
source_path = Path('.github/makegood-source.html')
soup = BeautifulSoup(source_path.read_text(),'html.parser')
for node in list(soup.find_all(string=True)):
    if node.parent.name in ('script','style'): continue
    value = str(node).replace('People. Culture. Practice.','People. Culture. Possibilities.').replace('PEOPLE. CULTURE. PRACTICE.','PEOPLE. CULTURE. POSSIBILITIES.')
    if value != str(node): node.replace_with(value)
brandtext = soup.select_one('.brandtext')
brandtext.clear()
for i,word in enumerate(('People.','Culture.','Possibilities.')):
    if i: brandtext.append(soup.new_tag('br'))
    brandtext.append(word)
about_heading = soup.select_one('#about .about-copy h2')
about_heading.clear()
about_heading.append('People. Culture.')
about_heading.append(soup.new_tag('br'))
about_heading.append('Possibilities.')
for node in soup.select('#home .stage-caption, #home .hero-note'):
    node.decompose()
for node in soup.select('#services .service-label'):
    node.name = 'h2'
for node in soup.select('.approach-item h3, .inquiry h3'):
    node.name = 'h2'
for field_name,auto in [('name','name'),('email','email'),('organization','organization')]:
    field = soup.select_one('[name="'+field_name+'"]')
    if field: field['autocomplete'] = auto
form = soup.select_one('#inquiry-form')
note = soup.select_one('.inquiry .form-note')
if form and note:
    note['id'] = 'inquiry-form-note'
    form['aria-describedby'] = 'inquiry-form-note'
source_path.write_text(str(soup))

builder_path = Path('.github/scripts/build-makegood-multipage.py')
builder = builder_path.read_text()
builder = re.sub(r"REV = '[^']+'", 'REV = '+repr(REV), builder)
builder = builder.replace('content="#F7EDDF"','content="#FAF7F2"').replace('sunrise-accents-2026-09-30','sunrise-v1.4-20261001')
builder = builder.replace('href="{prefix}sunrise.css"','href="{prefix}sunrise.css?v={REV}"')
if 'href="{prefix}palette.css?v={REV}"' not in builder:
    builder = builder.replace('<script>document.documentElement.classList.add', '<link rel="stylesheet" href="{prefix}palette.css?v={REV}"><script>document.documentElement.classList.add',1)
builder = builder.replace('<p>Choose the support that fits what you are working through.</p>','')
builder = builder.replace('People. Culture. Practice.','People. Culture. Possibilities.')
# Mission/vision become semantic second-level headings after the About H1.
builder = builder.replace("heading = SOURCE.new_tag('h3')", "heading = SOURCE.new_tag('h2')")
builder = builder.replace('- `sunrise.css` and `brand-update.css`: existing design and approved color extension.', '- `sunrise.css` and `brand-update.css`: cleaned layout styles.\n- `palette.css`: authoritative v1.4 colors, page treatments and accessibility refinements.')
builder_path.write_text(builder)

verifier_path = Path('.github/scripts/verify-makegood.py')
verify = verifier_path.read_text()
verify = verify.replace("['pages.css','pages.js','brand-update.css','makegood-sunrise.svg']", "['sunrise.css','pages.css','pages.js','brand-update.css','palette.css','makegood-sunrise.svg']")
verify = re.sub(r"pairs = \[\('#183F35'.*?\]\n", "pairs = [('#1F2E2A','#FAF7F2'),('#2E3A8C','#FAF7F2'),('#2E7D7A','#FAF7F2'),('#1F2E2A','#C9B4DA')]\n", verify)
verify = verify.replace("{'--evergreen':'#183F35','--mulberry':'#4A213A','--clay':'#974B36','--sage':'#D7DDCB'}", "{'--charcoal':'#1F2E2A','--indigo':'#2E3A8C','--teal':'#2E7D7A','--lilac':'#C9B4DA'}")
verifier_path.write_text(verify)
(ROOT/'brand-palette.json').write_text(json.dumps({'version':'1.4','revision':REV,'descriptor':approved['descriptor'],'colors':PALETTE,'source':'MakeGood_Brand_Guide_v1_4.pdf, approved visual palette; descriptor updated by LT on 1 October 2026','homepage_logo_caption':None,'homepage_logo_background':'#1F2E2A'},indent=2)+'\n')
print('Applied exact v1.4 palette, descriptor, copy removals and semantic heading changes.')
