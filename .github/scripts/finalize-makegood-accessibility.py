"""Respect successful cache revalidation and keep default-size service filters compact."""
from pathlib import Path
p=Path('.github/scripts/verify-makegood-accessibility.py')
s=p.read_text()
assert 'response.status==200' in s
# WebKit can expose 304 on a valid cached navigation. Page content and revision
# remain independently checked, so accepting revalidation does not bypass tests.
s=s.replace('response.status==200','response.status in (200,304)').replace('navigation.value.status==200','navigation.value.status in (200,304)')
p.write_text(s)
p=Path('makegood/site.css');s=p.read_text();assert '11rem' in s
p.write_text(s.replace('min(100%,11rem)','min(100%,9rem)'))
