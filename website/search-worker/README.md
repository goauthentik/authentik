# Search worker

A Cloudflare Worker that answers the documentation sites' search queries from a copy of the search index in D1. The three sites can query it instead of downloading the index into the browser: with the worker, a search costs a few kilobytes of JSON rather than the 2.2 MB the browser otherwise fetches on the first search.

The worker runs the same query code as the browser, `docusaurus-theme/search/query.mjs`, so the two paths rank identically. The browser falls back to its own copy of the index when a request to the worker fails.

This directory is its own pnpm workspace, outside the website workspace, so a website install does not download wrangler and the workerd runtime (about 175 MB). Install it with `pnpm --dir website/search-worker install`.

## Endpoints

| Path                                          | Response                                                                                                                                                                 |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `GET /search?q=<text>&site=<label>&limit=<n>` | The search response the modal renders. `site` names the site making the request (`Documentation`, `Integrations`, `API`) so its pages rank first. `limit` is at most 20. |
| `GET /health`                                 | The current slot, the commit the index was built from and its record count.                                                                                              |

Search responses are cached at the edge for five minutes. The worker answers requests from `goauthentik.io` and its subdomains, from `*.netlify.app` deploy previews, and from `localhost` and `127.0.0.1` on any port; `src/origins.ts` holds the list. Any other origin gets the response without an `Access-Control-Allow-Origin` header, and the browser then falls back to its own copy of the index.

## How the index is updated

`.github/workflows/website-search-index.yml` runs on every merge to `main` that changes a page, the index code, the worker or `schema.yml`.

1. It asks D1 which of the two table slots, `a` or `b`, the worker is serving (`pnpm run slot`, which runs `scripts/next-slot.ts`). Before the first import the pointer table does not exist and the answer is `a`. Any other failure to read the pointer, such as a bad credential, stops the run rather than guessing a slot.
2. It builds the SQL script for the other slot: `pnpm --dir website run build:search --d1 <slot>`.
3. It imports the script with `wrangler d1 execute DB --remote --file`. The script drops and recreates that slot's tables, fills them, and as its last statement flips the pointer in `search_current`. A reader therefore never sees a half-written index.

The same workflow redeploys the worker first when its code, or the query code it shares with the browser, changed.

Each documentation site's Netlify build also writes the browser-side copy of the index, and Netlify rebuilds a site only when that site's own directory or the theme changes. The browser-side copy of another site's pages can therefore be older than the hosted index; it is only used as the fallback.

## First-time setup

1. Create the database: `pnpm --dir website/search-worker exec wrangler d1 create authentik-docs-search`, and put the id it prints into `database_id` in `wrangler.jsonc`.
2. Add the repository secrets `CLOUDFLARE_API_TOKEN` (a token with Workers Scripts and D1 edit permissions) and `CLOUDFLARE_ACCOUNT_ID`.
3. Run the workflow once from the Actions tab (`workflow_dispatch`) to deploy the worker and import the first index.
4. Point the sites at the worker: set the build environment variable `AK_DOCS_SEARCH_ENDPOINT` to `https://<worker-host>/search` in each Netlify site's settings. A build without the variable, such as the `website/Dockerfile` image or a checkout with no network, ships the browser-side index and searches without a server.

## Local development

```shell
pnpm --dir website/search-worker install
pnpm --dir website run build:search --d1 a
pnpm --dir website/search-worker exec wrangler d1 execute DB --local --file ../build/search/search-index.a.sql
pnpm --dir website/search-worker run dev
```

Then `GET http://localhost:8787/search?q=ldap%20outpost&site=Documentation`. `pnpm --dir website/search-worker run check` type-checks the worker and runs its tests.
