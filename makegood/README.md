# MakeGood Co. standalone website

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
