"""Apply the approved community-first editorial and navigation changes only."""
from pathlib import Path
from bs4 import BeautifulSoup
import json
ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'makegood'
REV = '20261009-community-pathways-1'
changed = []
def load(name):
    return BeautifulSoup((SITE / name).read_text(), 'html.parser')
def fragment(html):
    return BeautifulSoup(html, 'html.parser')
def save(name, doc):
    (SITE / name).write_text(str(doc))
    changed.append(name)

# Only links change on Home; approved text and the absence of portraits remain.
doc = load('index.html')
home_text = doc.select_one('main').get_text(' ', strip=True)
for category, anchor in [('erg','erg-services-heading'),('presence','leadership-services-heading')]:
    a = doc.select_one(f'.home-service a[href="services.html?category={category}"]')
    assert a is not None, category
    a['href'] += '#' + anchor
assert home_text == doc.select_one('main').get_text(' ', strip=True)
assert not doc.select('.home-portraits, img[src*="founder"]')
save('index.html', doc)

# Four starting points and the same nine packages.
doc = load('services.html')
intro = doc.select_one('.section-intro')
intro.select_one('.lede').string = 'Build employee communities people want to take part in, support the people leading them, and work through the decisions that shape everyday experience.'
intro.append(fragment('<p class="small">The services below focus on program design, advice, and facilitated workshops—not event logistics or production. Each service page sets out what is included.</p>'))
card = doc.select_one('#guide-assess-heading').parent
card.select_one('p').string = 'Understand what people need from your ERG program—and what gets in the way.'
card = doc.select_one('#guide-build-heading').parent
card.select_one('p').string = 'Give community ideas a path forward with clear roles, sponsor support, and planning.'
card = doc.select_one('#guide-advice-heading').parent
card['aria-labelledby'] = 'guide-leadership-heading'
card.select_one('h3')['id'] = 'guide-leadership-heading'
card.select_one('h3').string = 'Our leaders and teams need support.'
card.select_one('p').string = 'Build trust, navigate difficult conversations, and make clearer decisions together.'
card.select_one('a')['href'] = 'services.html?category=presence#leadership-services-heading'
card.select_one('a span').string = 'Explore leadership support'
doc.select_one('#service-options-heading')['tabindex'] = '-1'
for category, anchor in [('erg','erg-services-heading'),('presence','leadership-services-heading'),('individual','coaching-services-heading')]:
    heading = doc.select_one(f'[data-group="{category}"] .group-heading h2')
    heading['id'] = anchor
    heading['tabindex'] = '-1'
doc.select_one('[data-group="erg"] .group-intro').string = 'Shape your ERG program around the people taking part: what they care about, how they can contribute, and what keeps them connected. Clear roles, sponsor support, and practical planning give that community room to grow.'
updates = {
 'erg-portfolio-diagnostic': ('Understand what your community needs next.', 'Listen to employee and leader experiences, review sponsorship and participation, and set priorities for a program people can help shape.'),
 'erg-operating-model-build': ('Give community ideas a path forward.', 'Turn community priorities into clear roles, sponsor guidance, and planning and budget tools—so leaders can put ideas into practice.'),
 'fractional-erg-office': ('Support the person supporting your community.', 'Senior advice on priorities, sponsorship, and one operating issue at a time. Help your program owner support the community while your team keeps daily administration.'),
 'practice-lab': ('Practice leading with your community in mind.', 'Work through community advocacy, sponsor conversations, or shared decisions in a focused ERG-leader or sponsor workshop. Leave with actions for the next 30 days.'),
 'presence-lab': ('Make room for people to contribute.', 'Three workshops on communication, decisions, trust, and disagreements—with team agreements that give people a clearer voice in how they work together.')
}
for key, (hook, description) in updates.items():
    offer = doc.select_one('#offer-' + key)
    offer.select_one('.offer-hook').string = hook
    offer.select_one('.offer-hook').find_next_sibling('p').string = description
for a in doc.select('a[href="services.html?category=presence"]'):
    a['href'] += '#leadership-services-heading'
doc.body.append(doc.new_tag('script', src='service-navigation.js?v=' + REV, defer=''))
assert len(doc.select('.service-guide-option')) == 4 and len(doc.select('.offer')) == 9
save('services.html', doc)

# Detail-page benefits change, but inclusions, exclusions and prices do not.
details = {
 'erg-portfolio-diagnostic': ('Understand what your employee community needs—and where support is falling short.', 'For organizations with unclear employee resource group (ERG) responsibilities, inconsistent practices, or overloaded leaders. We listen to employee and leader experiences and review sponsorship, resources, and participation to identify what helps people contribute and what gets in the way.'),
 'erg-operating-model-build': ('Give community priorities a practical path from idea to action.', 'For an employee resource group (ERG) program with an existing diagnostic or a clearly understood problem. We build the operating guide and tools your team will use to connect employee priorities with clear roles, sponsor support, planning, and resources.'),
 'fractional-erg-office': ('Senior guidance for the person supporting your employee communities.', 'Work through ERG priorities, sponsor relationships, and one agreed operating issue at a time, so your program owner can better support the community. Your organization retains decision-making authority and handles daily administration.'),
 'practice-lab': ('Practice the conversations and decisions that help employee communities thrive.', 'Choose one group: employee resource group (ERG) leaders or executive sponsors. Work through real situations—such as advocating for a community need, clarifying a decision, or working with a sponsor—and agree on actions for the next 30 days.'),
 'presence-lab': ('Three workshops to help your leadership team build trust and work better together.', 'For an existing leadership or sponsor team working on communication, decisions, inclusion, disagreements, or trust. We connect shared goals with team agreements and practices that make it easier for people to contribute.')
}
for key, (lead, detail) in details.items():
    name = f'services/{key}.html'
    doc = load(name)
    unchanged = [str(doc.select_one(s)) for s in ['.detail-summary','.detail-body']]
    block = doc.select_one('.detail-intro-block')
    block.select_one('.detail-intro').string = lead
    block.select_one('.detail-intro').find_next_sibling('p').string = detail
    doc.select_one('meta[name="description"]')['content'] = lead
    assert unchanged == [str(doc.select_one(s)) for s in ['.detail-summary','.detail-body']]
    save(name, doc)

# Practical expertise precedes biographies; full bios, mission and values remain.
doc = load('about.html')
bios_before = [str(x) for x in doc.select('.founder-card')]
values_before = [x.get_text(' ', strip=True) for x in doc.select('.purpose, .pillars')]
main = doc.select_one('main')
old_section = main.select_one(':scope > section.wrap.section')
about_intro = old_section.select_one('.about-intro').extract()
purpose = about_intro.select_one('.purpose').extract()
pillars = old_section.select_one('.pillars').extract()
founders = old_section.select_one('#founders').extract()
experience = main.select_one('#experience').extract()
about_intro.select_one('.lede').string = 'We help people build employee communities they can connect with, contribute to, and help shape.'
about_intro.select_one('.section-intro').find_next_sibling('p').string = 'Our expertise spans community building, organizational strategy, and investigations. We connect what people need with the relationships, resources, and decisions that make participation possible.'
about_intro.select_one('.about-logo').decompose()
about_intro['style'] = 'display:block;max-width:920px'
experience.select_one('.eyebrow').string = 'Our expertise'
h = experience.select_one('#experience-heading')
h.clear(); h.string = 'What this means for your community.'
h.attrs.pop('class', None)
ps = experience.select_one('.experience-intro').find_all('p', recursive=False)
ps[1].string = 'Experience building and supporting employee communities across a large, global workforce informs how we help people connect, contribute, and lead.'
for p in ps[2:]:
    p.decompose()
items = [
 ('Participation people can shape','We have supported employee communities from grassroots groups to global programs. We help you connect employee interests with meaningful ways to contribute.'),
 ('Support that turns ideas into action','Experience in program strategy and governance helps us clarify roles, resources, and sponsor relationships so community leaders can put ideas into practice.'),
 ('Leadership grounded in relationships','We bring experience developing and supporting ERG leaders—helping them build judgment, work with sponsors, and advocate for the people they represent.'),
 ('Listening that informs decisions','Our community-building and investigations experience helps us ask better questions, understand concerns, and turn employee insights into practical recommendations.')
]
for item, (title, text) in zip(experience.select('.experience-item'), items):
    item.select_one('h3').string = title
    item.select_one('p').string = text
founders['class'] = ['wrap','section']
new_intro = doc.new_tag('section', attrs={'class':'wrap section'})
new_intro.append(about_intro)
values = doc.new_tag('section', attrs={'class':'wrap section','aria-label':'What guides our work'})
values.append(purpose); values.append(pillars)
old_section.replace_with(new_intro)
new_intro.insert_after(experience); experience.insert_after(founders); founders.insert_after(values)
assert bios_before == [str(x) for x in doc.select('.founder-card')]
assert values_before == [x.get_text(' ', strip=True) for x in doc.select('.purpose, .pillars')]
save('about.html', doc)

# Optional, explicitly illustrative example, not a client claim.
doc = load('approach.html')
first = doc.select_one('.process-card .more')
first.append(fragment('<div class="approach-example"><h3>For example: people aren’t coming back.</h3><p class="small">Illustrative scenario—not a client case study.</p><p>An employee program attracts initial interest, but people rarely return. Rather than assume it needs more promotion, we look at whose interests shaped it, what makes participation difficult, and whether people have a say in what happens next.</p><p>Depending on what we learn, the next step might be a different format, more accessible timing, or a clearer way for participants to shape the program.</p></div>'))
style = doc.new_tag('style')
style.string = '.approach-example{border-top:1px solid var(--olive);margin-top:24px;padding-top:20px}.approach-example h3{font-size:1.125rem;line-height:1.4;margin-bottom:8px}'
doc.head.append(style)
save('approach.html', doc)

# The existing chooser regression follows the newly approved third pathway.
p = ROOT / '.github/workflows/verify-service-guide-spacing.yml'
text = p.read_text()
old = "'services/fractional-erg-office.html', 'services/coaching.html']"
assert old in text
text = text.replace(old, "'services.html', 'services/coaching.html']")
text = text.replace("assert urlsplit(page.url).path.endswith('/' + target)", "assert urlsplit(page.url).path.endswith('/' + target)\n                          if i == 2:\n                              assert page.locator('[data-filter=presence]').get_attribute('aria-pressed') == 'true'\n                              assert page.locator('.offer:visible').count() == 4")
p.write_text(text)
manifest = SITE / 'site-manifest.json'
m = json.loads(manifest.read_text()); m['editorial_revision'] = REV
manifest.write_text(json.dumps(m, indent=2) + '\n')
print(json.dumps({'revision':REV,'changed':changed,'preserved':['approved homepage copy','both founder biographies','mission and values','service scopes and pricing','contact form']},indent=2))
