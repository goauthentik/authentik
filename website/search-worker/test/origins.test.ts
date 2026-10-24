import assert from "node:assert/strict";
import { test } from "node:test";

import { allowedOrigin } from "../src/origins.ts";

test("the published sites, their subdomains, previews and a dev server are answered", () => {
    for (const origin of [
        "https://docs.goauthentik.io",
        "https://integrations.goauthentik.io",
        "https://api.goauthentik.io",
        "https://version-2026-10.goauthentik.io",
        "https://goauthentik.io",
        "https://deploy-preview-26976--authentik-docs.netlify.app",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://localhost",
    ]) {
        assert.equal(allowedOrigin(origin), origin, origin);
    }
});

test("any other origin is refused", () => {
    for (const origin of [
        "https://goauthentik.io.example.com",
        "https://example.com",
        "http://docs.goauthentik.io",
        "https://netlify.app",
        "https://a.b.netlify.app",
        "null",
        "",
    ]) {
        assert.equal(allowedOrigin(origin), null, origin);
    }
});
