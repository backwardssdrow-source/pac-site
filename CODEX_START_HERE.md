# Codex: start here for the Make Good site update

This branch exists specifically for the In Good Company → Make Good website update.

## Editable source

Open:

`make-good-source/index.html`

This is a readable copy of the existing single-page site source. It was copied from the repository's current human-editable source at:

`in-good-company-preview/index.html`

Do **not** use the compressed `site-payload-*.js` files as the primary editing target.

## Relevant deployment context

- Repository: `backwardssdrow-source/pac-site`
- Working branch: `make-good-site-update`
- Current readable source: `in-good-company-preview/index.html`
- Easier canonical working copy on this branch: `make-good-source/index.html`
- Current live deployment: `gh-pages/in-good-company-preview/`
- Current public preview: `https://backwardssdrow-source.github.io/pac-site/in-good-company-preview/#home`

The site is static HTML with hash-based service routes. Existing GitHub Actions under `.github/workflows/` handle older expansion, pricing, and verification steps.

## Codex task

Use `make-good-source/index.html` as the canonical editable source for the Make Good update. Preserve the current visual design and six service routes, rename all current-facing In Good Company branding to Make Good, apply the approved founding pricing and scope, stage—but do not publish—the proposed starter offers, create the `/make-good/` deployment route, and retain the legacy route as a hash-preserving redirect.

Before editing, inspect the current `gh-pages` deployment so later pricing and scope updates are not lost. After editing, make the build/deployment process generate GitHub Pages from this readable canonical source rather than requiring manual edits to compressed payload files.
