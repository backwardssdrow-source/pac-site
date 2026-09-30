# MakeGood Co. standalone website

The site has six main pages and nine service-detail pages. Navigation uses real HTML URLs; JavaScript only enhances menus, filters, legacy redirects and the explicitly unsent inquiry preview.

The approved Sunrise logo, palette, pricing and service scopes are preserved. The circular hero badge is removed from the markup.

## Sources
- `.github/makegood-source.html`: approved content snapshot before the multipage migration.
- `.github/scripts/build-makegood-multipage.py`: deterministic page builder (requires BeautifulSoup4).
- `sunrise.css` and `brand-update.css`: existing design and approved color extension.
- `pages.css` and `pages.js`: multipage layout and progressive enhancements.

Edit the snapshot or builder for copy changes, then regenerate to keep shared navigation consistent. Do not restore the original single-page navigation or load `sunrise.js` on these pages.

## Preview limitations
The inquiry preview sends nothing, stores nothing, and makes no booking or charge. A user may explicitly copy the draft or save a text file to their own device.
