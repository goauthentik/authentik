# Layer 3 v1 — Code-Mode MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the local stdio **code-mode** MCP server in `authentik-agent-marketplace/mcp-servers/code-mode/`: `search` over a live OpenAPI spec + a sandboxed `execute` / `execute_write` that runs agent code against an authenticated `ak.request(...)` helper.

**Architecture:** Three MCP tools backed by four pure units — config (env), schema (load + `$ref` deref + search), client (`ak.request` authed fetch with a read-only verb guard), sandbox (`node:vm` exposing only `ak` + `console`). `execute_write` uses a deterministic two-call confirm (preview → confirm token) instead of MCP elicitation, so it works identically on Claude Code and Cursor. The server self-loads the running instance's schema at startup (zero-maintenance).

**Tech Stack:** Node ≥24 (global `fetch`, `node:vm`, `node:test`), ESM `.mjs` + JSDoc types (no build step — matches `@goauthentik/docusaurus-theme`), `@modelcontextprotocol/sdk`, `zod`, `yaml`.

**Working repo:** `/Users/teffen/Projects/authentik-agent-marketplace` (a SEPARATE git repo from `authentik`). All paths below are relative to it. Commits land in this repo.

## Global Constraints

- Server lives under `mcp-servers/code-mode/` (the existing `mcp-servers/*` npm workspace).
- Language: ESM `.mjs` with JSDoc `@param`/`@returns`/`@typedef` types. **No build step** — `.mcp.json` runs the source entry directly with `node`. Repo is `"type": "module"`.
- Node floor: **≥24** (repo `engines`). Use global `fetch`, `node:vm`, `node:test`, `node:crypto`.
- Type-checked under `@goauthentik/tsconfig` (NodeNext, `strict: true`, `noUncheckedIndexedAccess: true`). JSDoc must satisfy it; verify with `npx tsc --noEmit -p mcp-servers/code-mode/tsconfig.json`.
- Test runner: `node --test mcp-servers/code-mode/src/<file>.test.mjs`. No live authentik needed — tests use a vendored schema fixture and a `node:http` mock server.
- Three tools only: `search`, `execute`, `execute_write`. No tool-per-endpoint.
- Auth/config via env: `AUTHENTIK_URL` (e.g. `https://id.example.com`) + `AUTHENTIK_TOKEN`. The token carries the admin's own permissions; the server enforces only the read-only/write split + confirm.
- `execute` binding is GET/HEAD/OPTIONS only. `execute_write` allows all verbs but requires a matching confirm token. The sandbox exposes ONLY `ak` + `console` — no `fetch`, `require`, `process`, `fs`.
- authentik schema paths are relative to base path `/api/v3` (e.g. spec path `/core/users/` → URL `${AUTHENTIK_URL}/api/v3/core/users/`).
- Stdout is reserved for the MCP protocol; all logging goes to **stderr** (`console.error`), never stdout.

---

### Task 1: Scaffold the `code-mode` server package

**Files:**

- Create: `mcp-servers/code-mode/package.json`
- Create: `mcp-servers/code-mode/tsconfig.json`
- Create: `mcp-servers/code-mode/src/version.mjs`
- Test: `mcp-servers/code-mode/src/version.test.mjs`

**Interfaces:**

- Produces: `SERVER_NAME = "authentik-code-mode"` and `SERVER_VERSION = "0.1.0"` from `version.mjs`.

- [ ] **Step 1: Write the failing test**

```js
import assert from "node:assert/strict";
// mcp-servers/code-mode/src/version.test.mjs
import { test } from "node:test";

import { SERVER_NAME, SERVER_VERSION } from "./version.mjs";

test("server identity constants", () => {
    assert.equal(SERVER_NAME, "authentik-code-mode");
    assert.match(SERVER_VERSION, /^\d+\.\d+\.\d+$/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test mcp-servers/code-mode/src/version.test.mjs`
Expected: FAIL — `Cannot find module './version.mjs'`.

- [ ] **Step 3: Create the package files**

`mcp-servers/code-mode/package.json`:

```json
{
    "name": "@goauthentik/mcp-code-mode",
    "version": "0.1.0",
    "private": true,
    "type": "module",
    "bin": { "authentik-code-mode": "./src/index.mjs" },
    "exports": { ".": "./src/index.mjs" },
    "dependencies": {
        "@modelcontextprotocol/sdk": "^1.18.0",
        "yaml": "^2.8.1",
        "zod": "^3.25.0"
    }
}
```

`mcp-servers/code-mode/tsconfig.json`:

```json
{
    "extends": "@goauthentik/tsconfig",
    "compilerOptions": {
        "checkJs": true,
        "allowJs": true,
        "noEmit": true,
        "composite": false,
        "declaration": false,
        "types": ["node"]
    },
    "include": ["src/**/*.mjs"]
}
```

`mcp-servers/code-mode/src/version.mjs`:

```js
/** @file Server identity constants. */
export const SERVER_NAME = "authentik-code-mode";
export const SERVER_VERSION = "0.1.0";
```

- [ ] **Step 4: Install deps and run the test**

Run: `pnpm install` (from repo root — installs the new workspace)
Run: `node --test mcp-servers/code-mode/src/version.test.mjs`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/code-mode/package.json mcp-servers/code-mode/tsconfig.json mcp-servers/code-mode/src/version.mjs mcp-servers/code-mode/src/version.test.mjs pnpm-lock.yaml
git commit -m "feat(code-mode): scaffold MCP server package"
```

---

### Task 2: Config loader (env validation)

**Files:**

- Create: `mcp-servers/code-mode/src/config.mjs`
- Test: `mcp-servers/code-mode/src/config.test.mjs`

**Interfaces:**

- Produces: `loadConfig(env) => { baseUrl: string, token: string }` — reads `AUTHENTIK_URL` + `AUTHENTIK_TOKEN`, strips a trailing slash from the URL, throws a clear `Error` if either is missing/empty.

- [ ] **Step 1: Write the failing test**

```js
import assert from "node:assert/strict";
// mcp-servers/code-mode/src/config.test.mjs
import { test } from "node:test";

import { loadConfig } from "./config.mjs";

test("loadConfig reads and normalizes env", () => {
    const cfg = loadConfig({ AUTHENTIK_URL: "https://id.example.com/", AUTHENTIK_TOKEN: "ak-tok" });
    assert.equal(cfg.baseUrl, "https://id.example.com");
    assert.equal(cfg.token, "ak-tok");
});

test("loadConfig throws when URL missing", () => {
    assert.throws(() => loadConfig({ AUTHENTIK_TOKEN: "x" }), /AUTHENTIK_URL/);
});

test("loadConfig throws when token missing", () => {
    assert.throws(() => loadConfig({ AUTHENTIK_URL: "https://id.example.com" }), /AUTHENTIK_TOKEN/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test mcp-servers/code-mode/src/config.test.mjs`
Expected: FAIL — `Cannot find module './config.mjs'`.

- [ ] **Step 3: Write minimal implementation**

```js
// mcp-servers/code-mode/src/config.mjs
/** @file Environment configuration for the code-mode server. */

/**
 * @typedef {object} AKConfig
 * @property {string} baseUrl authentik base URL, no trailing slash.
 * @property {string} token authentik API token.
 */

/**
 * @param {Record<string, string | undefined>} env
 * @returns {AKConfig}
 */
export function loadConfig(env) {
    const url = env.AUTHENTIK_URL?.trim();
    const token = env.AUTHENTIK_TOKEN?.trim();
    if (!url) throw new Error("AUTHENTIK_URL is required (e.g. https://id.example.com)");
    if (!token) throw new Error("AUTHENTIK_TOKEN is required (an authentik API token)");
    return { baseUrl: url.replace(/\/+$/, ""), token };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test mcp-servers/code-mode/src/config.test.mjs`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/code-mode/src/config.mjs mcp-servers/code-mode/src/config.test.mjs
git commit -m "feat(code-mode): env config loader"
```

---

### Task 3: Schema — `$ref` deref + `searchOperations`

**Files:**

- Create: `mcp-servers/code-mode/src/schema.mjs`
- Create (fixture): `mcp-servers/code-mode/src/__fixtures__/schema.yml`
- Test: `mcp-servers/code-mode/src/schema.test.mjs`

**Interfaces:**

- Produces:
    - `derefSchema(spec) => spec` — returns the spec with internal `$ref` (`#/components/...`) resolved inline, cycle-safe (a revisited ref becomes `{ $ref: "<original>" }` to break loops).
    - `searchOperations(spec, query, limit = 20) => Array<{ method, path, operationId, summary, tags, parameters, requestBody, responses }>` — case-insensitive match of `query` tokens against `path + operationId + summary + tags`; returns at most `limit` operations with their (deref'd) param/request/response slices.

- [ ] **Step 1: Create the fixture**

```yaml
# mcp-servers/code-mode/src/__fixtures__/schema.yml
openapi: 3.0.3
info:
    title: authentik
    version: 2026.8.0
paths:
    /core/users/:
        get:
            operationId: core_users_list
            summary: List users
            tags: [core]
            parameters:
                - name: search
                  in: query
                  schema: { type: string }
            responses:
                "200":
                    content:
                        application/json:
                            schema: { $ref: "#/components/schemas/User" }
    /stages/captcha/:
        post:
            operationId: stages_captcha_create
            summary: Create a captcha stage
            tags: [stages]
            requestBody:
                content:
                    application/json:
                        schema: { $ref: "#/components/schemas/CaptchaStage" }
            responses:
                "201":
                    content:
                        application/json:
                            schema: { $ref: "#/components/schemas/CaptchaStage" }
components:
    schemas:
        User:
            type: object
            properties:
                pk: { type: integer }
                username: { type: string }
        CaptchaStage:
            type: object
            properties:
                name: { type: string }
                public_key: { type: string }
                private_key: { type: string }
```

- [ ] **Step 2: Write the failing test**

```js
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
// mcp-servers/code-mode/src/schema.test.mjs
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { derefSchema, searchOperations } from "./schema.mjs";

import { parse } from "yaml";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const SPEC = derefSchema(
    parse(readFileSync(resolve(__dirname, "__fixtures__/schema.yml"), "utf-8")),
);

test("derefSchema inlines internal $refs", () => {
    const op = SPEC.paths["/core/users/"].get;
    assert.equal(
        op.responses["200"].content["application/json"].schema.properties.username.type,
        "string",
    );
});

test("searchOperations matches by summary/tag/path and returns slices", () => {
    const hits = searchOperations(SPEC, "captcha stage");
    assert.equal(hits.length, 1);
    assert.equal(hits[0].method, "POST");
    assert.equal(hits[0].path, "/stages/captcha/");
    assert.equal(hits[0].operationId, "stages_captcha_create");
    assert.ok(hits[0].requestBody.content["application/json"].schema.properties.public_key);
});

test("searchOperations returns [] when nothing matches", () => {
    assert.deepEqual(searchOperations(SPEC, "nonexistent-zzz"), []);
});

test("searchOperations honors the limit", () => {
    assert.ok(searchOperations(SPEC, "e", 1).length <= 1);
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `node --test mcp-servers/code-mode/src/schema.test.mjs`
Expected: FAIL — `Cannot find module './schema.mjs'`.

- [ ] **Step 4: Write minimal implementation**

```js
// mcp-servers/code-mode/src/schema.mjs
/** @file OpenAPI schema loading, $ref dereferencing, and operation search. */

const HTTP_METHODS = ["get", "put", "post", "delete", "patch", "head", "options"];

/**
 * Resolve a single `#/a/b/c` JSON pointer against the root document.
 * @param {any} root
 * @param {string} ref
 * @returns {any}
 */
function resolvePointer(root, ref) {
    const parts = ref.replace(/^#\//, "").split("/");
    let node = root;
    for (const part of parts) {
        node = node?.[part];
        if (node === undefined) return undefined;
    }
    return node;
}

/**
 * Return the spec with internal `$ref`s inlined. Cycle-safe: a ref already on
 * the current resolution stack is left as `{ $ref }` to break the loop.
 * @param {any} spec
 * @returns {any}
 */
export function derefSchema(spec) {
    const seen = new Set();
    /** @param {any} node @returns {any} */
    const walk = (node) => {
        if (node === null || typeof node !== "object") return node;
        if (Array.isArray(node)) return node.map(walk);
        if (typeof node.$ref === "string") {
            if (seen.has(node.$ref)) return { $ref: node.$ref };
            seen.add(node.$ref);
            const resolved = walk(resolvePointer(spec, node.$ref));
            seen.delete(node.$ref);
            return resolved ?? node;
        }
        /** @type {Record<string, any>} */
        const out = {};
        for (const [k, v] of Object.entries(node)) out[k] = walk(v);
        return out;
    };
    return walk(spec);
}

/**
 * Search operations by free-text query over path + operationId + summary + tags.
 * @param {any} spec A deref'd OpenAPI document.
 * @param {string} query
 * @param {number} [limit]
 * @returns {Array<object>}
 */
export function searchOperations(spec, query, limit = 20) {
    const tokens = query.toLowerCase().split(/\s+/).filter(Boolean);
    /** @type {Array<{ score: number, op: object }>} */
    const scored = [];
    for (const [path, item] of Object.entries(spec.paths ?? {})) {
        for (const method of HTTP_METHODS) {
            const op = /** @type {any} */ (item)[method];
            if (!op) continue;
            const haystack = [
                path,
                op.operationId ?? "",
                op.summary ?? "",
                (op.tags ?? []).join(" "),
            ]
                .join(" ")
                .toLowerCase();
            const score = tokens.filter((t) => haystack.includes(t)).length;
            if (score === 0) continue;
            scored.push({
                score,
                op: {
                    method: method.toUpperCase(),
                    path,
                    operationId: op.operationId,
                    summary: op.summary,
                    tags: op.tags ?? [],
                    parameters: op.parameters ?? [],
                    requestBody: op.requestBody,
                    responses: op.responses,
                },
            });
        }
    }
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, limit).map((s) => s.op);
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `node --test mcp-servers/code-mode/src/schema.test.mjs`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add mcp-servers/code-mode/src/schema.mjs mcp-servers/code-mode/src/schema.test.mjs mcp-servers/code-mode/src/__fixtures__
git commit -m "feat(code-mode): schema deref + operation search"
```

---

### Task 4: `ak.request` client (authed fetch + read-only guard)

**Files:**

- Create: `mcp-servers/code-mode/src/client.mjs`
- Test: `mcp-servers/code-mode/src/client.test.mjs`

**Interfaces:**

- Consumes: `AKConfig` from `config.mjs` (shape `{ baseUrl, token }`).
- Produces: `createAk(config, { allowWrites }) => { request(method, path, opts?) }` where `opts = { query?: Record<string,string|number>, body?: unknown }`. Builds `${baseUrl}/api/v3${path}`, sends `Authorization: Bearer <token>`, returns `{ status: number, data: unknown }`. When `allowWrites` is false, a non-GET/HEAD/OPTIONS method throws `Error("writes are disabled in this context; use execute_write")` BEFORE any network call.

- [ ] **Step 1: Write the failing test**

```js
import assert from "node:assert/strict";
import { createServer } from "node:http";
// mcp-servers/code-mode/src/client.test.mjs
import { test } from "node:test";

import { createAk } from "./client.mjs";

/** Spin up a throwaway HTTP server capturing the last request. */
async function withMock(handler, fn) {
    const server = createServer(handler);
    await new Promise((r) => server.listen(0, r));
    const { port } = server.address();
    try {
        return await fn(`http://127.0.0.1:${port}`);
    } finally {
        server.close();
    }
}

test("request performs an authenticated GET and parses JSON", async () => {
    await withMock(
        (req, res) => {
            assert.equal(req.headers.authorization, "Bearer tok");
            assert.equal(req.url, "/api/v3/core/users/?search=alice");
            res.setHeader("content-type", "application/json");
            res.end(JSON.stringify({ ok: true }));
        },
        async (baseUrl) => {
            const ak = createAk({ baseUrl, token: "tok" }, { allowWrites: false });
            const out = await ak.request("GET", "/core/users/", { query: { search: "alice" } });
            assert.equal(out.status, 200);
            assert.deepEqual(out.data, { ok: true });
        },
    );
});

test("read-only client rejects a write before any network call", async () => {
    const ak = createAk({ baseUrl: "http://127.0.0.1:1", token: "tok" }, { allowWrites: false });
    await assert.rejects(
        () => ak.request("POST", "/stages/captcha/", { body: {} }),
        /writes are disabled/,
    );
});

test("write-enabled client sends a POST body", async () => {
    await withMock(
        (req, res) => {
            let chunks = "";
            req.on("data", (c) => (chunks += c));
            req.on("end", () => {
                assert.equal(req.method, "POST");
                assert.deepEqual(JSON.parse(chunks), { name: "cap" });
                res.statusCode = 201;
                res.setHeader("content-type", "application/json");
                res.end(JSON.stringify({ pk: 1 }));
            });
        },
        async (baseUrl) => {
            const ak = createAk({ baseUrl, token: "tok" }, { allowWrites: true });
            const out = await ak.request("POST", "/stages/captcha/", { body: { name: "cap" } });
            assert.equal(out.status, 201);
            assert.deepEqual(out.data, { pk: 1 });
        },
    );
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test mcp-servers/code-mode/src/client.test.mjs`
Expected: FAIL — `Cannot find module './client.mjs'`.

- [ ] **Step 3: Write minimal implementation**

```js
// mcp-servers/code-mode/src/client.mjs
/** @file Authenticated `ak.request` helper bound into the sandbox. */

/** @import { AKConfig } from "./config.mjs" */

const READ_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);

/**
 * @param {AKConfig} config
 * @param {{ allowWrites: boolean }} opts
 * @returns {{ request: (method: string, path: string, opts?: { query?: Record<string, string|number>, body?: unknown }) => Promise<{ status: number, data: unknown }> }}
 */
export function createAk(config, { allowWrites }) {
    /**
     * @param {string} method
     * @param {string} path
     * @param {{ query?: Record<string, string|number>, body?: unknown }} [opts]
     */
    async function request(method, path, opts = {}) {
        const verb = method.toUpperCase();
        if (!allowWrites && !READ_METHODS.has(verb)) {
            throw new Error(
                `writes are disabled in this context; use execute_write (attempted ${verb} ${path})`,
            );
        }
        const url = new URL(`${config.baseUrl}/api/v3${path}`);
        for (const [k, v] of Object.entries(opts.query ?? {})) {
            url.searchParams.set(k, String(v));
        }
        const res = await fetch(url, {
            method: verb,
            headers: {
                "authorization": `Bearer ${config.token}`,
                "content-type": "application/json",
                "accept": "application/json",
            },
            body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
        });
        const text = await res.text();
        let data;
        try {
            data = text ? JSON.parse(text) : null;
        } catch {
            data = text;
        }
        return { status: res.status, data };
    }
    return { request };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test mcp-servers/code-mode/src/client.test.mjs`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/code-mode/src/client.mjs mcp-servers/code-mode/src/client.test.mjs
git commit -m "feat(code-mode): authenticated ak.request with read-only guard"
```

---

### Task 5: Sandbox (`node:vm`, only `ak` + `console`)

**Files:**

- Create: `mcp-servers/code-mode/src/sandbox.mjs`
- Test: `mcp-servers/code-mode/src/sandbox.test.mjs`

**Interfaces:**

- Produces: `runInSandbox(code, ak, { timeoutMs = 30000 }) => Promise<{ result: unknown, logs: string[] }>` — runs `code` as the body of an `async` function in a `vm` context whose only globals are `ak` and `console` (log/error/warn push to `logs`). No `fetch`, `require`, `process`, `globalThis` escapes. `result` is the code's `return` value (JSON-cloned to a plain value). Throws if the code throws or exceeds the timeout.

- [ ] **Step 1: Write the failing test**

```js
import assert from "node:assert/strict";
// mcp-servers/code-mode/src/sandbox.test.mjs
import { test } from "node:test";

import { runInSandbox } from "./sandbox.mjs";

const fakeAk = { request: async (m, p) => ({ status: 200, data: { m, p } }) };

test("runs code against ak and returns the value", async () => {
    const { result } = await runInSandbox(
        `const r = await ak.request("GET", "/core/users/"); return r.data;`,
        fakeAk,
        {},
    );
    assert.deepEqual(result, { m: "GET", p: "/core/users/" });
});

test("captures console output", async () => {
    const { logs } = await runInSandbox(`console.log("hello", 42);`, fakeAk, {});
    assert.ok(logs.some((l) => l.includes("hello") && l.includes("42")));
});

test("fetch, require, and process are not available in the sandbox", async () => {
    const { result } = await runInSandbox(
        `return [typeof fetch, typeof require, typeof process];`,
        fakeAk,
        {},
    );
    assert.deepEqual(result, ["undefined", "undefined", "undefined"]);
});

test("propagates errors thrown by the code", async () => {
    await assert.rejects(() => runInSandbox(`throw new Error("boom");`, fakeAk, {}), /boom/);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test mcp-servers/code-mode/src/sandbox.test.mjs`
Expected: FAIL — `Cannot find module './sandbox.mjs'`.

- [ ] **Step 3: Write minimal implementation**

```js
// mcp-servers/code-mode/src/sandbox.mjs
/** @file In-process code sandbox: only `ak` + `console` are reachable. */

import vm from "node:vm";

/**
 * Run agent code in a constrained vm context.
 *
 * The context object's own properties ARE the sandbox globals — Node builtins
 * (`fetch`, `require`, `process`, `fs`) are absent, so `ak.request` is the only
 * egress. This is not a hardened security boundary against a hostile actor (vm
 * is escapable); the binding is the boundary, per the design's trust model.
 *
 * @param {string} code
 * @param {{ request: Function }} ak
 * @param {{ timeoutMs?: number }} opts
 * @returns {Promise<{ result: unknown, logs: string[] }>}
 */
export async function runInSandbox(code, ak, { timeoutMs = 30000 }) {
    /** @type {string[]} */
    const logs = [];
    const record = (...args) =>
        logs.push(args.map((a) => (typeof a === "string" ? a : JSON.stringify(a))).join(" "));
    const sandbox = {
        ak,
        console: { log: record, error: record, warn: record, info: record },
    };
    const context = vm.createContext(sandbox);
    const wrapped = `(async () => {\n${code}\n})()`;
    const script = new vm.Script(wrapped, { filename: "agent-code.mjs" });
    const promise = script.runInContext(context, { timeout: timeoutMs });
    const result = await promise;
    // Force a plain serializable value (and surface non-serializable results early).
    return { result: result === undefined ? null : JSON.parse(JSON.stringify(result)), logs };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test mcp-servers/code-mode/src/sandbox.test.mjs`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/code-mode/src/sandbox.mjs mcp-servers/code-mode/src/sandbox.test.mjs
git commit -m "feat(code-mode): node:vm sandbox exposing only ak + console"
```

---

### Task 6: Tools — `search`, `execute`, `execute_write` (two-call confirm)

**Files:**

- Create: `mcp-servers/code-mode/src/tools.mjs`
- Test: `mcp-servers/code-mode/src/tools.test.mjs`

**Interfaces:**

- Consumes: `searchOperations` (schema.mjs), `createAk` (client.mjs), `runInSandbox` (sandbox.mjs).
- Produces: `createTools({ spec, config }) => { search, execute, executeWrite, confirmTokenFor }` where:
    - `search({ query, limit? }) => { operations }` — wraps `searchOperations`.
    - `execute({ code }) => { result, logs }` — runs `code` with a **read-only** `ak`.
    - `confirmTokenFor(code) => string` — deterministic 8-char token (sha256 of code).
    - `executeWrite({ code, confirm? }) => { status: "needs_confirmation", token, preview } | { result, logs }` — when `confirm` is absent or wrong, returns `needs_confirmation` with the token + a preview (the code) and does NOT run; when `confirm === confirmTokenFor(code)`, runs `code` with a **write-enabled** `ak`.

- [ ] **Step 1: Write the failing test**

```js
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createServer } from "node:http";
import { resolve } from "node:path";
// mcp-servers/code-mode/src/tools.test.mjs
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { derefSchema } from "./schema.mjs";
import { createTools } from "./tools.mjs";

import { parse } from "yaml";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const SPEC = derefSchema(
    parse(readFileSync(resolve(__dirname, "__fixtures__/schema.yml"), "utf-8")),
);

async function withMock(handler, fn) {
    const server = createServer(handler);
    await new Promise((r) => server.listen(0, r));
    try {
        return await fn(`http://127.0.0.1:${server.address().port}`);
    } finally {
        server.close();
    }
}

test("search returns matching operations", () => {
    const tools = createTools({ spec: SPEC, config: { baseUrl: "http://x", token: "t" } });
    const { operations } = tools.search({ query: "list users" });
    assert.ok(operations.some((o) => o.operationId === "core_users_list"));
});

test("execute runs read-only code", async () => {
    await withMock(
        (req, res) => res.end(JSON.stringify([{ username: "alice" }])),
        async (baseUrl) => {
            const tools = createTools({ spec: SPEC, config: { baseUrl, token: "t" } });
            const { result } = await tools.execute({
                code: `return (await ak.request("GET","/core/users/")).data;`,
            });
            assert.deepEqual(result, [{ username: "alice" }]);
        },
    );
});

test("execute blocks writes (read-only binding)", async () => {
    const tools = createTools({
        spec: SPEC,
        config: { baseUrl: "http://127.0.0.1:1", token: "t" },
    });
    await assert.rejects(
        () =>
            tools.execute({
                code: `return await ak.request("POST","/stages/captcha/",{body:{}});`,
            }),
        /writes are disabled/,
    );
});

test("execute_write requires a matching confirm token, then runs", async () => {
    await withMock(
        (req, res) => {
            res.statusCode = 201;
            res.end(JSON.stringify({ pk: 7 }));
        },
        async (baseUrl) => {
            const tools = createTools({ spec: SPEC, config: { baseUrl, token: "t" } });
            const code = `return (await ak.request("POST","/stages/captcha/",{body:{name:"c"}})).data;`;
            const first = await tools.executeWrite({ code });
            assert.equal(first.status, "needs_confirmation");
            assert.equal(first.token, tools.confirmTokenFor(code));
            const second = await tools.executeWrite({ code, confirm: first.token });
            assert.deepEqual(second.result, { pk: 7 });
        },
    );
});

test("execute_write rejects a wrong confirm token without running", async () => {
    const tools = createTools({
        spec: SPEC,
        config: { baseUrl: "http://127.0.0.1:1", token: "t" },
    });
    const code = `return await ak.request("POST","/stages/captcha/",{body:{}});`;
    const out = await tools.executeWrite({ code, confirm: "wrongtok" });
    assert.equal(out.status, "needs_confirmation");
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test mcp-servers/code-mode/src/tools.test.mjs`
Expected: FAIL — `Cannot find module './tools.mjs'`.

- [ ] **Step 3: Write minimal implementation**

```js
// mcp-servers/code-mode/src/tools.mjs
/** @file The three code-mode tools: search, execute, execute_write. */

import { createHash } from "node:crypto";

import { createAk } from "./client.mjs";
import { runInSandbox } from "./sandbox.mjs";
import { searchOperations } from "./schema.mjs";

/** @import { AKConfig } from "./config.mjs" */

/**
 * @param {{ spec: any, config: AKConfig }} deps
 */
export function createTools({ spec, config }) {
    /** @param {string} code */
    const confirmTokenFor = (code) => createHash("sha256").update(code).digest("hex").slice(0, 8);

    /** @param {{ query: string, limit?: number }} args */
    const search = ({ query, limit }) => ({ operations: searchOperations(spec, query, limit) });

    /** @param {{ code: string }} args */
    const execute = async ({ code }) => {
        const ak = createAk(config, { allowWrites: false });
        return runInSandbox(code, ak, {});
    };

    /** @param {{ code: string, confirm?: string }} args */
    const executeWrite = async ({ code, confirm }) => {
        const token = confirmTokenFor(code);
        if (confirm !== token) {
            return {
                status: "needs_confirmation",
                token,
                preview: code,
                message:
                    "This code will run with WRITE access to the authentik instance. " +
                    `Re-call execute_write with confirm: "${token}" to run it unchanged.`,
            };
        }
        const ak = createAk(config, { allowWrites: true });
        return runInSandbox(code, ak, {});
    };

    return { search, execute, executeWrite, confirmTokenFor };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test mcp-servers/code-mode/src/tools.test.mjs`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add mcp-servers/code-mode/src/tools.mjs mcp-servers/code-mode/src/tools.test.mjs
git commit -m "feat(code-mode): search/execute/execute_write with two-call write confirm"
```

---

### Task 7: Server entry — MCP wiring + startup schema load

**Files:**

- Create: `mcp-servers/code-mode/src/load-schema.mjs`
- Create: `mcp-servers/code-mode/src/index.mjs`
- Test: `mcp-servers/code-mode/src/load-schema.test.mjs`

**Interfaces:**

- Consumes: `loadConfig` (config.mjs), `derefSchema` (schema.mjs), `createTools` (tools.mjs), `SERVER_NAME`/`SERVER_VERSION` (version.mjs).
- Produces: `fetchSchema(config) => Promise<spec>` — GETs `${baseUrl}/api/v3/schema/` with the bearer token, parses YAML or JSON, returns the **deref'd** spec; on network failure logs to stderr and throws. `index.mjs` is the executable entry: loads config, fetches+derefs schema, builds tools, registers them on an `McpServer`, connects `StdioServerTransport`.

- [ ] **Step 1: Write the failing test**

```js
import assert from "node:assert/strict";
import { createServer } from "node:http";
// mcp-servers/code-mode/src/load-schema.test.mjs
import { test } from "node:test";

import { fetchSchema } from "./load-schema.mjs";

test("fetchSchema GETs /api/v3/schema/ and returns a deref'd spec", async () => {
    const server = createServer((req, res) => {
        assert.equal(req.url, "/api/v3/schema/");
        assert.equal(req.headers.authorization, "Bearer t");
        res.setHeader("content-type", "application/json");
        res.end(
            JSON.stringify({
                openapi: "3.0.3",
                paths: {
                    "/core/users/": {
                        get: { operationId: "core_users_list", summary: "List users" },
                    },
                },
                components: {},
            }),
        );
    });
    await new Promise((r) => server.listen(0, r));
    try {
        const spec = await fetchSchema({
            baseUrl: `http://127.0.0.1:${server.address().port}`,
            token: "t",
        });
        assert.equal(spec.paths["/core/users/"].get.operationId, "core_users_list");
    } finally {
        server.close();
    }
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `node --test mcp-servers/code-mode/src/load-schema.test.mjs`
Expected: FAIL — `Cannot find module './load-schema.mjs'`.

- [ ] **Step 3: Write `load-schema.mjs`**

```js
// mcp-servers/code-mode/src/load-schema.mjs
/** @file Fetch the running instance's OpenAPI schema at startup. */

import { derefSchema } from "./schema.mjs";

import { parse } from "yaml";

/** @import { AKConfig } from "./config.mjs" */

/**
 * @param {AKConfig} config
 * @returns {Promise<any>} deref'd OpenAPI document
 */
export async function fetchSchema(config) {
    const url = `${config.baseUrl}/api/v3/schema/`;
    const res = await fetch(url, {
        headers: { authorization: `Bearer ${config.token}`, accept: "application/json" },
    });
    if (!res.ok) {
        throw new Error(`failed to fetch schema from ${url}: HTTP ${res.status}`);
    }
    const text = await res.text();
    // The endpoint serves JSON by default; parse() handles both JSON and YAML.
    return derefSchema(parse(text));
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `node --test mcp-servers/code-mode/src/load-schema.test.mjs`
Expected: PASS (1 test).

- [ ] **Step 5: Write `index.mjs` (the MCP entry)**

```js
// mcp-servers/code-mode/src/index.mjs
#!/usr/bin/env node
/** @file authentik code-mode MCP server (stdio). */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

import { SERVER_NAME, SERVER_VERSION } from "./version.mjs";
import { loadConfig } from "./config.mjs";
import { fetchSchema } from "./load-schema.mjs";
import { createTools } from "./tools.mjs";

/** Wrap a tool result object as MCP text content. */
const asContent = (value) => ({ content: [{ type: "text", text: JSON.stringify(value, null, 2) }] });

async function main() {
    const config = loadConfig(process.env);
    const spec = await fetchSchema(config);
    const tools = createTools({ spec, config });

    const server = new McpServer({ name: SERVER_NAME, version: SERVER_VERSION });

    server.tool(
        "search",
        "Search authentik's API: free-text query over path/operationId/summary/tags. Returns matching operations with their parameter, request, and response schemas. Use this to discover what to call before writing code.",
        { query: z.string(), limit: z.number().int().positive().optional() },
        async (args) => asContent(tools.search(args)),
    );

    server.tool(
        "execute",
        "Run JavaScript against the live authentik instance with a READ-ONLY `ak.request(method, path, { query, body })` client (GET/HEAD/OPTIONS only). `return` a value to receive it. Compose multiple reads in one block.",
        { code: z.string() },
        async (args) => asContent(await tools.execute(args)),
    );

    server.tool(
        "execute_write",
        "Run JavaScript with a WRITE-ENABLED `ak.request(...)` client. Two-step: call once with { code } to receive a confirm token + preview, then call again with { code, confirm } (same code) to run it. Reads and writes may be mixed in one block.",
        { code: z.string(), confirm: z.string().optional() },
        async (args) => asContent(await tools.executeWrite(args)),
    );

    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error(`${SERVER_NAME} ${SERVER_VERSION} ready (${config.baseUrl})`);
}

main().catch((err) => {
    console.error(`${SERVER_NAME} failed to start: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(1);
});
```

- [ ] **Step 6: Smoke-test the entry boots and lists tools**

Create `mcp-servers/code-mode/src/index.smoke.test.mjs`:

```js
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { resolve } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const ENTRY = resolve(__dirname, "index.mjs");

test("server starts, serves schema, and responds to tools/list over stdio", async () => {
    // Mock instance serving a minimal schema.
    const inst = createServer((req, res) => {
        res.setHeader("content-type", "application/json");
        res.end(JSON.stringify({ openapi: "3.0.3", paths: {}, components: {} }));
    });
    await new Promise((r) => inst.listen(0, r));
    const baseUrl = `http://127.0.0.1:${inst.address().port}`;

    const child = spawn("node", [ENTRY], {
        env: { ...process.env, AUTHENTIK_URL: baseUrl, AUTHENTIK_TOKEN: "t" },
        stdio: ["pipe", "pipe", "pipe"],
    });
    try {
        let out = "";
        child.stdout.on("data", (d) => (out += d));
        const send = (msg) => child.stdin.write(JSON.stringify(msg) + "\n");
        send({
            jsonrpc: "2.0",
            id: 1,
            method: "initialize",
            params: {
                protocolVersion: "2025-06-18",
                capabilities: {},
                clientInfo: { name: "t", version: "0" },
            },
        });
        send({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });
        await new Promise((r) => setTimeout(r, 1500));
        assert.match(out, /"search"/);
        assert.match(out, /"execute_write"/);
    } finally {
        child.kill();
        inst.close();
    }
});
```

Run: `node --test mcp-servers/code-mode/src/index.smoke.test.mjs`
Expected: PASS (1 test). If flaky on timing, raise the `setTimeout` to 3000ms — do not reduce assertions.

- [ ] **Step 7: Type-check the whole server**

Run: `npx tsc --noEmit -p mcp-servers/code-mode/tsconfig.json`
Expected: no errors. Fix any JSDoc type errors before committing.

- [ ] **Step 8: Commit**

```bash
git add mcp-servers/code-mode/src/load-schema.mjs mcp-servers/code-mode/src/load-schema.test.mjs mcp-servers/code-mode/src/index.mjs mcp-servers/code-mode/src/index.smoke.test.mjs
git commit -m "feat(code-mode): MCP stdio entry + startup schema fetch"
```

---

### Task 8: Register the server + README (🛑 GATE: captcha pivot, mock)

**Files:**

- Modify: `.mcp.json`
- Modify: `hooks/hooks.json`
- Modify: `README.md` (the MCP servers table)
- Create: `mcp-servers/code-mode/README.md`
- Test: `mcp-servers/code-mode/src/pivot.test.mjs`

**Interfaces:**

- Consumes: everything above (end-to-end).

- [ ] **Step 1: Write the captcha pivot integration test (mock instance)**

```js
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createServer } from "node:http";
import { resolve } from "node:path";
// mcp-servers/code-mode/src/pivot.test.mjs
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { derefSchema } from "./schema.mjs";
import { createTools } from "./tools.mjs";

import { parse } from "yaml";

const __dirname = fileURLToPath(new URL(".", import.meta.url));
const SPEC = derefSchema(
    parse(readFileSync(resolve(__dirname, "__fixtures__/schema.yml"), "utf-8")),
);

test("PIVOT: discover + create a captcha stage in one confirmed write block", async () => {
    const calls = [];
    const inst = createServer((req, res) => {
        calls.push(`${req.method} ${req.url}`);
        res.statusCode = 201;
        res.setHeader("content-type", "application/json");
        res.end(JSON.stringify({ pk: "stage-1", name: "captcha" }));
    });
    await new Promise((r) => inst.listen(0, r));
    try {
        const tools = createTools({
            spec: SPEC,
            config: { baseUrl: `http://127.0.0.1:${inst.address().port}`, token: "t" },
        });

        // 1. The agent discovers the endpoint.
        const { operations } = tools.search({ query: "create captcha stage" });
        assert.ok(operations.some((o) => o.operationId === "stages_captcha_create"));

        // 2. The agent writes one block; first call returns a confirm token.
        const code = `
            const stage = (await ak.request("POST", "/stages/captcha/", { body: { name: "captcha" } })).data;
            return stage.pk;
        `;
        const first = await tools.executeWrite({ code });
        assert.equal(first.status, "needs_confirmation");

        // 3. Confirmed run performs the write.
        const second = await tools.executeWrite({ code, confirm: first.token });
        assert.equal(second.result, "stage-1");
        assert.ok(calls.includes("POST /api/v3/stages/captcha/"));
    } finally {
        inst.close();
    }
});
```

Run: `node --test mcp-servers/code-mode/src/pivot.test.mjs`
Expected: PASS — proves the L1→L2→L3 instance loop (discover → write → confirm) end-to-end against a mock.

- [ ] **Step 2: Run the whole server suite + type-check**

Run: `node --test mcp-servers/code-mode/src/*.test.mjs`
Expected: all PASS.
Run: `npx tsc --noEmit -p mcp-servers/code-mode/tsconfig.json`
Expected: no errors.

- [ ] **Step 3: Register in `.mcp.json`**

Replace the empty `mcpServers` with:

```json
{
    "mcpServers": {
        "authentik-code-mode": {
            "command": "node",
            "args": ["${CLAUDE_PLUGIN_ROOT}/mcp-servers/code-mode/src/index.mjs"],
            "env": {
                "AUTHENTIK_URL": "${AUTHENTIK_URL}",
                "AUTHENTIK_TOKEN": "${AUTHENTIK_TOKEN}"
            }
        }
    }
}
```

- [ ] **Step 4: Register the deps-install hook in `hooks/hooks.json`**

Replace the empty `hooks` with a `SessionStart` entry that installs the server's runtime deps (matches the pattern described in the repo README):

```json
{
    "hooks": {
        "SessionStart": [
            {
                "matcher": "*",
                "hooks": [
                    {
                        "type": "command",
                        "command": "cd \"${CLAUDE_PLUGIN_ROOT}/mcp-servers/code-mode\" && npm install --omit=dev --no-audit --no-fund"
                    }
                ]
            }
        ]
    }
}
```

- [ ] **Step 5: Write `mcp-servers/code-mode/README.md`**

````markdown
# authentik code-mode MCP server

Exposes authentik's API to an agent as **code**, not as hundreds of tools:

- `search(query)` — find API operations (path/summary/tags) with their schemas.
- `execute(code)` — run JS with a **read-only** `ak.request(method, path, { query, body })`.
- `execute_write(code[, confirm])` — run JS with write access; two-step confirm.

## Auth

Set two environment variables (the token carries your own permissions):

```bash
export AUTHENTIK_URL="https://id.example.com"
export AUTHENTIK_TOKEN="ak-…"   # Directory → Tokens → create
```

The server fetches `${AUTHENTIK_URL}/api/v3/schema/` at startup, so discovery
always matches your instance's version.

## Example

```
search({ query: "list failed logins events" })
execute({ code: `return (await ak.request("GET","/events/events/",{query:{action:"login_failed",ordering:"-created",page_size:10}})).data;` })
```
````

- [ ] **Step 6: Add the server to the root `README.md` MCP servers table**

Add this row under the `| Server | Backs skill | Tool |` table header:

```markdown
| [`code-mode`](mcp-servers/code-mode/) | `ak-admin` (instance ops) | `search`, `execute`, `execute_write` |
```

- [ ] **Step 7: Commit**

```bash
git add .mcp.json hooks/hooks.json README.md mcp-servers/code-mode/README.md mcp-servers/code-mode/src/pivot.test.mjs
git commit -m "feat(code-mode): register server, hook, docs; captcha pivot test"
```

---

## Out of scope (separate efforts)

- **L2 wiring** — adding the steering line to the `ak-admin` skills (the L2→L3 seam) and pointing skills at the `llms.txt` entry points (L2→L1). Tracked as its own small plan; depends only on Layer 1 (shipped) and this server's tool names.
- **L3 v2** — the authentik-native OAuth endpoint (RBAC-as-authorization, event-log audit). Separate spec + plan, after this v1 pivot passes.

## Self-Review

**1. Spec coverage (Layer 3 v1 section of the design):**

- `search` over `schema.yml`: Task 3 (+ live fetch Task 7). ✅
- `execute` read-only sandbox: Tasks 4 (guard) + 5 (sandbox) + 6 (tool). ✅
- `execute_write` with confirmation: Task 6 (two-call confirm — the chosen client-agnostic resolution of the spec's elicitation open-question). ✅
- Binding-is-the-boundary sandbox (only `ak`+`console`, no fs/fetch): Task 5. ✅
- Env auth (`AUTHENTIK_URL`/`AUTHENTIK_TOKEN`): Task 2. ✅
- Schema-at-startup from `/api/v3/schema/`: Task 7. ✅
- Three tools only, `.mcp.json` + hook registration: Tasks 7–8. ✅
- Captcha pivot (mock): Task 8. ✅
- `@goauthentik/api` optional (generic fetch used): Task 4. ✅

**2. Placeholder scan:** No TBD/TODO; every code step is complete; every command has an expected result. ✅

**3. Type consistency:** `AKConfig {baseUrl, token}` is consistent across config/client/load-schema/tools. `createAk(config,{allowWrites}).request(method,path,opts)` matches its callers in tools.mjs. `createTools({spec,config})` returns `{search,execute,executeWrite,confirmTokenFor}` used identically in index.mjs and tests. `runInSandbox(code,ak,opts)` consistent. ✅

**Known follow-ups (non-blocking):** `vm` is not a hardened sandbox (documented; binding-is-the-boundary per design); `search` ranking is a simple token-overlap count (sufficient for v1; revisit if recall is poor on the real 1141-operation spec); the smoke/pivot tests use a fixed `setTimeout` (raise if flaky, never weaken assertions).
