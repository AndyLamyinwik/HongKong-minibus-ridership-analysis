# Research Website Deployment

The static research publication is released from [`site/`](../site/) in the public [GitHub repository](https://github.com/AndyLamyinwik/hong-kong-minibus-ridership-analysis). The approved design, historical snapshot and analytical definitions remain unchanged.

**[Explore the Interactive Research Website](https://andylamyinwik.github.io/hong-kong-minibus-ridership-analysis/)** — publicly verified on **12 October 2026**.

## Verified initial deployment

The [initial release workflow](https://github.com/AndyLamyinwik/hong-kong-minibus-ridership-analysis/actions/runs/38204286899) completed both build and deployment successfully for commit `492bc3f31de71bb5b8a0a00e5ed5ce6accbda5d3`. GitHub's deployment record returned the public URL above and a successful `github-pages` status for that exact commit. Subsequent pushes use the same gated workflow; its [run history](https://github.com/AndyLamyinwik/hong-kong-minibus-ridership-analysis/actions/workflows/deploy-site.yml) identifies the currently deployed release.

Anonymous HTTP checks verified all **26 generated files**, including the homepage, scripts, CSS, fonts, licenses and JSON. Every SHA-256 matched the local release build. The 36,628-byte JSON retained all seventeen source hashes. Ten navigation anchors resolved, and all thirteen GitHub documentation/repository links returned HTTP 200.

The public website was operated in the available Chromium browser at desktop and mobile sizes. All four SVG charts rendered; annual/index controls, recovery selection, share focus/year selection, fleet mode/measure/year selection and methodology disclosures responded with the validated values. No unexpected application errors or warnings were captured. The [website validation record](../site/docs/validation.md#phase-6c--public-release) gives the scope and results.

The local Python HTTP client encountered a TLS connection error for the two DATA.GOV.HK links. Both the official catalogue and terms pages were accessible through the web reader, so their authentic URLs were retained. This is a client-specific verification limit; the website serves its preserved research data from its own static artifact.

## Automated release

[`deploy-site.yml`](../.github/workflows/deploy-site.yml) runs on pushes to `main` and supports manual execution in GitHub Actions. It uses Node.js **24.19.0** and pnpm **11.25.0**, with the existing frontend lockfile and `pnpm install --frozen-lockfile`.

The build job verifies the deterministic static export, executes the isolated exporter contracts and all frontend tests, then runs Vite. Official GitHub checkout/Node/Pages actions and the pnpm setup action are pinned to verified commit IDs. The upload step includes **only `site/dist/`**. Dependencies, research inputs, local QA files and development caches are outside the website artifact.

The dependent deployment job uses `pages: write`, `id-token: write` and the `github-pages` environment. Build permissions are limited to source and Pages metadata reads. One deployment runs at a time. The environment URL comes from `steps.deployment.outputs.page_url`; a successful push alone is not deployment evidence.

The configuration follows [GitHub's custom Pages workflow guidance](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages) and [Vite's GitHub Pages deployment guidance](https://vite.dev/guide/static-deploy.html#github-pages).

## Repository path and source setting

The Vite base is **`/hong-kong-minibus-ridership-analysis/`**. Scripts, styles, fonts, the favicon and bundled data must resolve under that path. The site is a single HTML publication with section anchors. Its static data export requires no runtime preparation or analytical server.

GitHub Pages must use **GitHub Actions** as its source. To inspect or restore that setting, open repository **Settings → Pages → Build and deployment → Source → GitHub Actions**. The workflow must remain enabled and `main` must be permitted to deploy to `github-pages`.

## Verification and maintenance

Local release checks are `pnpm test` and `pnpm build` from `site/`, plus `python site/scripts/export_data.py --check` and `python site/tests/export_data_test.py` from the root. The original analytical suite follows its existing pinned environment and [reproduction prerequisites](data_reuse.md#download-the-dictionary-for-full-local-reproduction). Its specification PDF remains excluded from publication.

Before a release, inspect the staged file list and diff; preserve the validated data and research conclusions. After pushing, inspect both Actions jobs, the returned Pages URL and the intended commit. Verify public HTTP responses, built-asset hashes, JSON, all four charts, native controls, chapter navigation, attribution and desktop/mobile rendering. Verify the repository website field and README link separately.

The [website validation record](../site/docs/validation.md) retains earlier phase checks. The [metric provenance](../site/docs/metric_provenance.md) maps every website metric to preserved analytical outputs. The original Streamlit application remains separately documented for local use in [dashboard.md](dashboard.md); a Pages deployment does not establish Streamlit cloud compatibility.
