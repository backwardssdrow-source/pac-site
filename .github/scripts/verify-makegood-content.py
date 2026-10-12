"""Current multi-page content checks; no network requests or email sends."""
import html,json,os,re
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(os.environ.get('MAKEGOOD_ROOT',Path(__file__).resolve().parents[2])).resolve()
SITE=ROOT/'makegood'
M=json.loads((SITE/'site-manifest.json').read_text())

class Page(HTMLParser):
 def __init__(self,source):
  super().__init__();self.meta={};self.links=[];self.footer_links=[];self.ids=set();self.body={};self.in_footer=False;self.offers=0
  self.feed(source)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'offer' in a.get('class','').split():self.offers+=1
  if tag=='footer':self.in_footer=True
  if tag=='meta':
   key=a.get('name',a.get('property'))
   if key:
    assert key not in self.meta,('Duplicate metadata',key)
    self.meta[key]=a.get('content','')
  if tag=='link' and a.get('rel')=='canonical':self.canonical=a['href']
  if tag=='body':self.body=a
  if 'id' in a:
   assert a['id'] not in self.ids,('Duplicate ID',a['id'])
   self.ids.add(a['id'])
  if tag=='a':
   self.links.append(a.get('href',''))
   if self.in_footer:self.footer_links.append(a.get('href',''))
 def handle_endtag(self,tag):
  if tag=='footer':self.in_footer=False

def text(source):
 return ' '.join(html.unescape(re.sub(r'<[^>]+>',' ',source)).split())

assert len(M['pages'])==16 and len(set(M['pages']))==16,'Expected 16 separate pages, including Privacy'
assert set(M['pages'])=={str(p.relative_to(SITE)) for p in SITE.rglob('*.html')},'Manifest must match published HTML pages'
assert M['review_only'] is True and M['search_indexing'] is False,'Domain/indexing cutover is a separate decision'
assert M['inquiry_sends'] is True
assert M['expected']['index.html']['title']=='MakeGood Co. | People. Culture. Possibilities.'
pages={};sources={}
for route in M['pages']:
 source=(SITE/route).read_text();sources[route]=source;p=Page(source);pages[route]=p;expected=M['expected'][route]
 for tag,key in [('title','title'),('h1','h1')]:
  matches=re.findall(r'<'+tag+r'\b[^>]*>(.*?)</'+tag+r'>',source,re.S|re.I)
  assert len(matches)==1 and text(matches[0])==expected[key],(route,key)
 assert p.body.get('data-page')==route,(route,'data-page')
 assert p.meta.get('robots')=='noindex,nofollow',(route,'robots')
 assert p.meta.get('site-revision')==M['revision'],(route,'revision')
 assert p.meta.get('description'),(route,'description')
 canonical='https://backwardssdrow-source.github.io/pac-site/makegood/'+('' if route=='index.html' else route)
 assert p.canonical==canonical,(route,'canonical')
 for key,value in {'og:title':expected['title'],'og:description':p.meta['description'],'og:url':canonical,'og:site_name':'MakeGood Co.','og:type':'website','twitter:card':'summary','twitter:title':expected['title'],'twitter:description':p.meta['description'],'twitter:url':canonical}.items():
  assert p.meta.get(key)==value,(route,key)
 assert p.footer_links.count('../privacy.html' if '/' in route else 'privacy.html')==1,(route,'footer privacy link')

fees={'decision-session':['$1,250'],'practice-lab':['$2,500'],'erg-portfolio-diagnostic':['$9,000'],'erg-operating-model-build':['$18,000'],'fractional-erg-office':['$7,500 / month','$22,500 minimum'],'presence-scan':['$5,000'],'presence-lab':['$10,000'],'senior-presence-advisory':['$2,000 / month','$6,000 initial total','$3,500/month total','$10,500 initial total']}
for service,amounts in fees.items():
 route='services/'+service+'.html'
 for amount in amounts:assert amount in text(sources[route]),(route,amount)
for route in [p for p in M['pages'] if p.startswith('services/')]:
 service=Path(route).stem
 assert '../contact.html?service='+service in pages[route].links,(route,'inquiry path')
assert pages['services.html'].offers==M['service_count']==9
for phrase in ['first three contracts','first five paid Decision Sessions or Practice Labs combined','initial three-month term only','A positive review is not required.']:
 assert phrase in text(sources['faq.html']),('Founding terms',phrase)
assert 'Your fee is confirmed before you commit' in text(sources['services/coaching.html'])
assert 'contact-fallback' in pages['contact.html'].ids
assert 'mailto:info@makegoodco.com' in pages['contact.html'].links
assert 'private Google Workspace tracker' in text(sources['contact.html'])
assert 'privacy.html' in pages['contact.html'].links
assert 'mailto:info@makegoodco.com' in pages['privacy.html'].links
for p in SITE.rglob('*'):
 if p.suffix in ['.html','.js']:
  assert not re.search(r'\b(?:lt|travis)@makegoodco\.com\b',p.read_text(),re.I),('Private recipient in public source',p)

redirect=(ROOT/'in-good-company-preview/index.html').read_text()
assert '<title>MakeGood Co. | People. Culture. Possibilities.</title>' in redirect,'Legacy entry point title must stay current'
assert "location.replace('../makegood/'+location.search+location.hash)" in redirect,'Legacy redirect must preserve query and hash'
assert 'href="../makegood/"' in redirect,'Legacy redirect needs its no-JavaScript link'
for path in [SITE/'sunrise.js',ROOT/'in-good-company-preview/sunrise.js']:
 assert 'MakeGood Co. | People. Culture. Possibilities.' in path.read_text(),('Legacy script title',path)
 assert 'Services and Founding Pricing' not in path.read_text(),('Obsolete title',path)
print('PASS: 16 pages, current titles and social metadata, service fees and inquiry paths, private recipient separation, privacy links, email fallback, and legacy redirect.')
