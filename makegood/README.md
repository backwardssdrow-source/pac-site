# MakeGood Co. website

People. Culture. Possibilities.

## Current publication

The site is served from the `makegood/` directory on the `gh-pages` branch of `backwardssdrow-source/pac-site`:

https://backwardssdrow-source.github.io/pac-site/makegood/

It contains six main pages, nine service pages, and a Privacy page. Navigation uses separate HTML documents. Both founder biographies and portraits are present. Service prices, scope, and founding-rate eligibility terms are unchanged by the launch cleanup.

The current pages intentionally retain `noindex,nofollow` and GitHub Pages canonical URLs while the final domain is prepared. Page titles, descriptions, Open Graph/Twitter metadata, and the existing Sunrise SVG favicon are configured. No dedicated social-preview image is configured.

## Contact and privacy

The contact form is connected to a Google Apps Script sending service. Valid inquiries are saved in a private Google Workspace tracker, and the service requests email notifications to both founders. The site shows success only after a readable acceptance response containing the matching inquiry ID; acceptance does not prove receipt in either inbox.

After an uncertain response, retries with unchanged details reuse the same inquiry ID. Inquiry content is held in page memory and is not written to localStorage. The form includes a short privacy notice, a link to the Privacy page, and an email fallback. Booking and payments are not connected to the website.

Private notification recipients and the tracker ID belong in the private Apps Script configuration, never in this repository. The public fallback address is separate from those private settings.

## Domain cutover

MakeGood is currently a subdirectory of the PAC repository. Connecting this entire repository directly to `makegoodco.com` would serve the PAC website at the domain root, rather than the MakeGood homepage.

Prepare a MakeGood-only publishing root or dedicated site deployment before connecting that domain. No domain connection or new repository is part of this cleanup. At cutover, update canonical and sharing URLs, redirects, and the indexing settings together; retain `noindex,nofollow` until then. The corresponding automated checks must reflect the approved indexing state.

## Maintenance and verification

Current pages use `site.js`; `service-navigation.js` enhances the service chooser. Historical single-page scripts and compressed preview bundles are not the source of the current multi-page site. Avoid regenerating current pages from those older previews.

The former `in-good-company-preview/` entry point redirects to MakeGood and preserves its query string and hash. Automated website/readability checks cover navigation, mobile reflow, text enlargement, and the contact response contract. Contact requests in CI are intercepted so those checks do not send real inquiries. A separately authorized live test is required to verify the deployed sending service and actual inbox receipt.

