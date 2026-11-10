/**
 * @file Unit test setup: give Node the DOM globals Lit elements touch at import time.
 */

import * as shim from "@lit-labs/ssr-dom-shim";

for (const [name, value] of Object.entries(shim)) {
    if (!(name in globalThis)) {
        Object.defineProperty(globalThis, name, { value, configurable: true, writable: true });
    }
}

// The shim's window has no location, which code reading the URL expects.
if (typeof window !== "undefined" && !("location" in window)) {
    Object.defineProperty(window, "location", { value: new URL("http://localhost/") });
}
