import { LanguageCookieName, persistLocale, readPersistedLocale } from "#common/ui/locale/persist";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// `persistLocale` reads the web base path from the global; stub it so the test
// does not depend on a rendered `window.authentik`.
vi.mock("#common/global", () => ({
    globalAK: () => ({ api: { relBase: "/" } }),
}));

/**
 * Minimal `document.cookie` emulation: setting `name=value; attrs` upserts a single
 * cookie, and the getter serializes the jar back to `name=value; ...`, matching how a
 * browser exposes cookies to script.
 */
function installCookieJar() {
    const store = new Map<string, string>();
    let lastWrite = "";

    Object.defineProperty(globalThis, "document", {
        configurable: true,
        value: {
            get cookie() {
                return [...store.entries()].map(([k, v]) => `${k}=${v}`).join("; ");
            },
            set cookie(raw: string) {
                lastWrite = raw;
                const pair = raw.split(";")[0] ?? "";
                const eq = pair.indexOf("=");
                store.set(pair.slice(0, eq).trim(), pair.slice(eq + 1).trim());
            },
        },
    });

    return {
        get lastWrite() {
            return lastWrite;
        },
    };
}

describe("locale persistence", () => {
    let jar: ReturnType<typeof installCookieJar>;

    beforeEach(() => {
        jar = installCookieJar();
        vi.stubGlobal("location", { protocol: "http:" });
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    it("round-trips the persisted locale through the language cookie", () => {
        persistLocale("de-DE");

        expect(readPersistedLocale()).toBe("de-DE");
    });

    it("writes the Django language cookie scoped and same-site", () => {
        persistLocale("fr-FR");

        expect(jar.lastWrite).toContain(`${LanguageCookieName}=fr-FR`);
        expect(jar.lastWrite).toMatch(/path=\/(;|$)/i);
        expect(jar.lastWrite).toMatch(/samesite=lax/i);
        expect(jar.lastWrite).toMatch(/max-age=\d+/i);
        expect(jar.lastWrite).not.toMatch(/secure/i);
    });

    it("marks the cookie secure when served over HTTPS", () => {
        vi.stubGlobal("location", { protocol: "https:" });

        persistLocale("fr-FR");

        expect(jar.lastWrite).toMatch(/;\s*secure(;|$)/i);
    });

    it("returns null when no locale has been persisted", () => {
        expect(readPersistedLocale()).toBeNull();
    });

    it("decodes a percent-encoded cookie value", () => {
        // Written raw, as another encoder (e.g. the server) might have set it.
        document.cookie = `${LanguageCookieName}=zh%2DHans; path=/`;

        expect(readPersistedLocale()).toBe("zh-Hans");
    });
});
