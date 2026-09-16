/**
 * @file Loading of third-party CAPTCHA provider scripts.
 *
 * @remarks
 *
 * ## Content Security Policy
 *
 * Loading the provider bundle here — as a plain `<script src>` on the flow document — is
 * what makes the CAPTCHA stage compatible with a strict CSP. The previous implementation
 * built an HTML document per widget and handed it to an iframe, which forced three
 * concessions that no strict policy can make:
 *
 * - `script-src 'unsafe-inline'`, because the generated document carried inline `<script>`
 *   blocks for the provider callbacks and the `postMessage` bridge.
 * - `frame-src blob:`, because that document was served to the iframe as a blob URL.
 * - `document.write()` into `about:blank` for reCAPTCHA and hCaptcha, whose domain
 *   verification could not see the real origin through a blob URL.
 *
 * None of those remain. Providers are configured by passing callbacks to their own render
 * APIs, so no markup is generated and nothing is evaluated from a string.
 *
 * What a policy still has to allow is per-provider and derived from the stage's configured
 * `js_url` / `api_url`, which is why it belongs on the server rather than hardcoded here:
 *
 * - `script-src` — the origin of `js_url`.
 * - `frame-src` — the provider's challenge origin. Usually the `js_url` origin; reCAPTCHA
 *   also frames `https://www.google.com`.
 * - `connect-src` — the origin the widget reports back to, generally the `js_url` origin.
 * - `style-src 'unsafe-inline'` — reCAPTCHA and hCaptcha both set inline styles on the
 *   elements they inject. Turnstile and Cap do not.
 *
 * Note that `api_url` is called by the authentik server, not the browser, so it never needs
 * a CSP entry.
 */

import { ConsoleLogger } from "#logger/browser";

const logger = ConsoleLogger.prefix("flow:captcha:script");

/**
 * How long to wait for a provider's global to appear after its script reports `load`.
 *
 * Providers install their global synchronously during evaluation, so this only has to
 * absorb a stray microtask. Cap is the exception — it registers a custom element, and
 * `customElements.whenDefined` may settle a tick later.
 */
const GLOBAL_TIMEOUT = 5_000;

const POLL_INTERVAL = 50;

export interface LoadCaptchaScriptInit {
    url: URL;
    type: "classic" | "module";
    /**
     * Whether the provider's runtime API is present yet.
     */
    isAvailable: () => boolean;
}

/**
 * Scripts already requested by this document, keyed by resolved URL.
 *
 * Provider scripts are global singletons: requesting the same URL twice re-runs the
 * bootstrap and, for Turnstile in particular, leaves duplicate widgets behind. A flow can
 * show the same provider more than once (an identification stage with an embedded CAPTCHA
 * followed by a dedicated CAPTCHA stage), so the second stage has to reuse the first
 * stage's script rather than add its own.
 */
const pending = new Map<string, Promise<void>>();

function waitForGlobal(isAvailable: () => boolean): Promise<void> {
    if (isAvailable()) return Promise.resolve();

    return new Promise((resolve, reject) => {
        const deadline = Date.now() + GLOBAL_TIMEOUT;

        const poll = () => {
            if (isAvailable()) return resolve();

            if (Date.now() > deadline) {
                return reject(
                    new Error("CAPTCHA provider script loaded but never exposed its API."),
                );
            }

            setTimeout(poll, POLL_INTERVAL);
        };

        poll();
    });
}

function injectScript({ url, type }: LoadCaptchaScriptInit): Promise<void> {
    return new Promise((resolve, reject) => {
        const script = document.createElement("script");

        script.src = url.toString();
        script.async = true;

        if (type === "module") {
            script.type = "module";
        }

        script.addEventListener("load", () => resolve(), { once: true });
        script.addEventListener(
            "error",
            () => reject(new Error(`Failed to load CAPTCHA script from ${url.host}.`)),
            { once: true },
        );

        document.head.appendChild(script);
    });
}

/**
 * Load a provider's script, reusing an in-flight or completed load of the same URL.
 *
 * Resolves once the provider's runtime API is usable, not merely once the network request
 * finished.
 */
export function loadCaptchaScript(init: LoadCaptchaScriptInit): Promise<void> {
    const key = init.url.toString();

    const existing = pending.get(key);

    if (existing) {
        logger.debug(`Reusing in-flight load for ${key}`);
        return existing;
    }

    // A script element may already be present from a previous flow executor instance
    // within the same document, in which case there is nothing to inject.
    const alreadyInDocument = Iterator.from(document.querySelectorAll("script")).some(
        (script) => script.src === key,
    );

    const load = (alreadyInDocument ? Promise.resolve() : injectScript(init))
        .then(() => waitForGlobal(init.isAvailable))
        .catch((error: unknown) => {
            // A failed load must not be cached — the next stage deserves a fresh attempt.
            pending.delete(key);
            throw error;
        });

    pending.set(key, load);

    return load;
}
