# Search worker

A Cloudflare Worker that answers the documentation sites' search queries from a copy of the search index in D1. The three sites can query it instead of downloading the index into the browser: with the worker, a search costs a few kilobytes of JSON rather than the 2.2 MB the browser otherwise fetches on the first search.

The worker runs the same query code as the browser, `docusaurus-theme/search/query.mjs`, so the two paths rank identically. The browser falls back to its own copy of the index when a request to the worker fails.

## Endpoints

| Path                                          | Response                                                                                                                                                                 |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `GET /search?q=<text>&site=<label>&limit=<n>` | The search response the modal renders. `site` names the site making the request (`Documentation`, `Integrations`, `API`) so its pages rank first. `limit` is at most 20. |
| `GET /health`                                 | The current slot, the commit the index was built from and its record count.                                                                                              |

Responses carry `Access-Control-Allow-Origin: *` and are cached at the edge for five minutes.

## How the index is updated

`.github/workflows/website-search-index.yml` runs on every merge to `main` that changes a page, the index code, the worker or `schema.yml`. It reads which of the two table slots, `a` or `b`, the worker is serving, builds the SQL script for the other slot with `pnpm run build:search --d1 <slot>`, imports it with `wrangler d1 execute DB --remote --file`, and the script's last statement flips the pointer in `search_current`. A rebuild therefore never shows a reader a half-written index. The same workflow redeploys the worker when its code changes.

## First-time setup

1. Create the database: `pnpm exec wrangler d1 create authentik-docs-search`, and put the id it prints into `database_id` in `wrangler.jsonc`.
2. Add the repository secrets `CLOUDFLARE_API_TOKEN` (a token with Workers Scripts and D1 edit permissions) and `CLOUDFLARE_ACCOUNT_ID`.
3. Run the workflow once from the Actions tab (`workflow_dispatch`) to deploy the worker and import the first index.
4. Point the sites at the worker: set the build environment variable `AK_DOCS_SEARCH_ENDPOINT` to `https://<worker-host>/search` in each Netlify site's settings. A build without the variable, such as the `website/Dockerfile` image or a checkout with no network, ships the browser-side index and searches without a server.

## Local development

```shell
pnpm --dir website run build:search --d1 a
pnpm exec wrangler d1 execute DB --local --file ../build/search/search-index.a.sql
pnpm exec wrangler dev
```

Then `GET http://localhost:8787/search?q=ldap%20outpost&site=Documentation`.
