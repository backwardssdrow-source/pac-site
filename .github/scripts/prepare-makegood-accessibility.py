"""Prepare approved readability refinements; publishing remains a separate step."""
from pathlib import Path
from bs4 import BeautifulSoup
import re,json
ROOT=Path('.').resolve();S=ROOT/'makegood';REV='20261008-accessibility-1'
def relative_fonts(s):
 def convert(m):
  return m[1]+re.sub(r'([\d.]+)px',lambda n:f'{float(n[1])/16:g}rem',m[2])
 return re.sub(r'(font-size\s*:\s*)([^;}]+)',convert,s)
for name in ['site-base.css','site.css','home.css']:
 p=S/name;p.write_text(relative_fonts(p.read_text()))
p=S/'site.css';t=p.read_text().replace('site-base.css?v=20261007-separate-pages-2',f'site-base.css?v={REV}')
t+='''
/* Accessibility refinement: readable text, less visual weight, resilient reflow. */
html{font-size:100%;scroll-padding-top:calc(var(--nav-h) + 12px)}
body{line-height:1.65}
.nav-wrap{flex-wrap:wrap}
.navlinks{flex-wrap:wrap;max-width:100%}
main [id]{scroll-margin-top:12px}
main,section,article,aside,form,.section-intro,.hero-copy,.home-people-copy{min-width:0}
.button,.text-link,.home-founder-link,.service-guide-link,.breadcrumbs a,summary{min-height:44px}
.button,.filter,.menu-toggle,input,select,textarea{max-width:100%}
input,select,textarea{min-width:0}
input::placeholder,textarea::placeholder{color:var(--charcoal);opacity:1}
input:disabled,select:disabled,textarea:disabled,button:disabled{cursor:not-allowed}
.offer-hook{font-weight:400}
:where(a,button,input,select,textarea,summary){scroll-margin-block:12px}
.site-footer .footer-links{grid-template-columns:repeat(2,minmax(0,1fr));max-width:28rem;width:100%}
.site-footer .footer-links a{min-height:44px;border:0;background:transparent;justify-content:flex-start;text-align:left;padding:8px 4px}
.optional-context{margin:24px 0;padding:16px 0;border-block:1px solid var(--olive)}
.optional-context>summary{cursor:pointer;font-size:1.125rem;font-weight:600;line-height:1.5;padding:8px 32px 8px 0}
.optional-context[open]>summary{margin-bottom:20px}
.optional-context .maturity-grid{margin-top:8px}
.optional-context p{max-width:65ch}
.faq-group-heading{font-size:1.25rem;font-weight:600;line-height:1.4;margin:32px 0 12px}
.faq-group-heading:first-child{margin-top:16px}
html body[data-page] .service-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,11rem),1fr));gap:12px;max-width:54rem}
html body[data-page] .filter{font-size:1rem;min-height:48px;white-space:normal;border-radius:7px;padding:10px 12px}
html body[data-page] .filter[aria-pressed=true]{font-weight:600}
html body[data-page] .filter-status{max-width:65ch}
@media screen and (max-width:900px){
 /* The open menu stays in flow; it cannot cover the text or keyboard focus. */
 html body .site-header{position:relative}
 html.menu-ready body .site-header .navlinks.open{position:static;flex-basis:100%;width:100%;max-height:none;overflow:visible;padding:8px 0 12px;border:0}
 html{scroll-padding-top:12px}
 html body[data-page] .site-header .nav-wrap{flex-wrap:wrap}
 html body[data-page] .section-intro h1,html body[data-page] .detail-intro-block h1{font-size:2rem;line-height:1.25;font-weight:700;max-width:24ch}
 html body[data-page] .hero h1{font-size:2.25rem;line-height:1.25;font-weight:700}
 html body[data-page] h2{font-size:1.625rem;line-height:1.35;font-weight:600}
 html body[data-page] h3,html body[data-page] h4{font-size:1.25rem;line-height:1.4;font-weight:600}
 html body[data-page] .founder-card h3{font-size:1.625rem}
 html body[data-page] .faq-group-heading{font-size:1.25rem}
 html body[data-page] .lede,html body[data-page] .detail-intro{font-size:1.1875rem;line-height:1.65;font-weight:400}
 html body[data-page] .offer,html body[data-page] .founder-card,html body[data-page] .detail-summary{padding:22px 20px}
 html body[data-page] .offer-grid,html body[data-page] .founder-grid,html body[data-page] .contact-grid{grid-template-columns:minmax(0,1fr);gap:28px}
 html body[data-page] .footer-main{display:flex;flex-direction:column;align-items:flex-start;gap:20px}
 html body[data-page] .home-footer>.wrap{flex-wrap:wrap}
 html body[data-page] .home-footer .footer-links{width:auto;max-width:none}
 html body[data-page] .home-footer .footer-links a{padding:8px 0}
 html body[data-page] .fee-confirm{font-size:1.375rem;line-height:1.45;font-weight:600}
 html body[data-page] .scope-boundary{padding:20px}
 html body[data-page] .detail-grid{grid-template-columns:minmax(0,1fr)}
}
@media screen and (max-width:360px){
 html body[data-page] .hero h1{font-size:2.1875rem}
 html body[data-page] .wrap{width:calc(100% - 32px)}
}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation:none!important;transition:none!important}}
@media print{.optional-context>*{display:block!important}.optional-context>summary{list-style:none}}
'''
p.write_text(t)
p=S/'about.html';t=p.read_text();n=t.count('</p></div></div></article>');assert n==2,n;t=t.replace('</p></div></div></article>','</p></div></article>');p.write_text(t)
p=S/'services.html';s=BeautifulSoup(p.read_text(),'html.parser')
stages=s.select_one('#erg-stages');stages.find('h3').decompose();stages.name='details';stages['class']=['erg-stages','optional-context'];stages.attrs.pop('aria-labelledby',None)
summ=s.new_tag('summary');summ['id']='stages-heading';summ.string='Which stage is our ERG program at?';stages.insert(0,summ)
bridge=s.select_one('.erg-leadership-bridge');content=list(bridge.select('div')[1].contents);bridge.clear();bridge.name='details';bridge['class']=['optional-context'];bridge.attrs.pop('aria-labelledby',None)
summ=s.new_tag('summary');summ['id']='erg-leadership-heading';summ.string='How ERG support and leadership development fit together';bridge.append(summ)
for c in content:bridge.append(c)
filters=s.select_one('.service-filters');heading=s.new_tag('h2',id='service-options-heading');heading.string='Explore services';filters.insert_before(heading);filters['aria-labelledby']='service-options-heading';filters.attrs.pop('aria-label',None)
p.write_text(str(s))
p=S/'faq.html';s=BeautifulSoup(p.read_text(),'html.parser');q=s.select_one('.faq-list');items=q.find_all('details',recursive=False);assert len(items)==10,len(items)
groups=[('Getting started',[0,1,3,4,6]),('Fees and booking',[2,7,8]),('Working together',[5,9])]
for item in items:item.extract()
q.clear()
for title,inds in groups:
 h=s.new_tag('h2');h['class']='faq-group-heading';h.string=title;q.append(h)
 for i in inds:q.append(items[i])
p.write_text(str(s))
for p in S.rglob('*.html'):
 t=relative_fonts(p.read_text())
 t=re.sub(r'(site\.css|site\.js|home\.css)\?v=[^"\s<]+',lambda m:m[1]+'?v='+REV,t)
 t=re.sub(r'<meta\s+content="[^"]+"\s+name="site-revision"\s*/?>',f'<meta content="{REV}" name="site-revision"/>',t)
 p.write_text(t)
for p in S.rglob('*.html'):
 s=BeautifulSoup(p.read_text(),'html.parser');ids=[e['id'] for e in s.find_all(id=True)];assert len(ids)==len(set(ids)),p
m=json.loads((S/'site-manifest.json').read_text());m['revision']=REV
for key in m['expected']:m['expected'][key]['revision']=REV
(S/'site-manifest.json').write_text(json.dumps(m,indent=2)+'\n')
(ROOT/'.github/scripts/verify-makegood.py').write_text('"""Run the shared accessibility and navigation checks."""\nimport runpy\nfrom pathlib import Path\nrunpy.run_path(str(Path(__file__).with_name("verify-makegood-accessibility.py")), run_name="__main__")\n')
print('Accessibility changes prepared:',REV)
