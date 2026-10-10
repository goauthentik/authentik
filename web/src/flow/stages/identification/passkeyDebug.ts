/**
 * @file Temporary passkey autofill diagnostics. Drop this before merging.
 *   Every entry goes to the console as `authentik/passkey-debug` and is batched to
 *   `flows/-/passkey-debug/`, which writes it to the server log, so the order of events on a
 *   phone can be read without Web Inspector attached (attaching it changes the timing).
 */

import { globalAK } from "#common/global";

const pageID = Math.random().toString(36).slice(2, 10);
const endpoint = new URL("flows/-/passkey-debug/", globalAK().api.base).toString();

let queue: Record<string, unknown>[] = [];
let flushTimer = -1;

function flush(): void {
    clearTimeout(flushTimer);

    if (!queue.length) return;

    const body = JSON.stringify({
        page: pageID,
        url: location.pathname + location.search,
        userAgent: navigator.userAgent,
        entries: queue,
    });

    queue = [];
    navigator.sendBeacon(endpoint, new Blob([body], { type: "application/json" }));
}

function describeElement(element: EventTarget | Element | null): string | null {
    if (!(element instanceof Element)) return null;

    const name = element.getAttribute("name");

    return name ? `${element.localName}[name=${name}]` : element.localName;
}

/**
 * The element that really has focus, looking through shadow roots.
 */
export function deepActiveElement(): string | null {
    let active: Element | null = document.activeElement;

    while (active?.shadowRoot?.activeElement) {
        active = active.shadowRoot.activeElement;
    }

    return describeElement(active);
}

export function passkeyDebug(event: string, detail: Record<string, unknown> = {}): void {
    const entry = { t: Math.round(performance.now()), event, ...detail };

    console.info("authentik/passkey-debug", JSON.stringify(entry));

    queue.push(entry);
    clearTimeout(flushTimer);
    flushTimer = window.setTimeout(flush, 500);
}

passkeyDebug("module loaded", {
    userAgent: navigator.userAgent,
    navigationType:
        (performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined)
            ?.type ?? null,
});

if (typeof PublicKeyCredential !== "undefined" && "getClientCapabilities" in PublicKeyCredential) {
    PublicKeyCredential.getClientCapabilities()
        .then((capabilities) => passkeyDebug("client capabilities", { capabilities }))
        .catch((error: unknown) =>
            passkeyDebug("client capabilities failed", { error: `${error}` }),
        );
}

window.addEventListener("pageshow", (event) =>
    passkeyDebug("pageshow", { persisted: event.persisted }),
);

window.addEventListener("pagehide", (event) => {
    passkeyDebug("pagehide", { persisted: event.persisted });
    flush();
});

window.addEventListener("focus", () => passkeyDebug("window focus"));
window.addEventListener("blur", () => passkeyDebug("window blur"));

document.addEventListener("visibilitychange", () => {
    passkeyDebug("visibilitychange", { state: document.visibilityState });

    if (document.visibilityState === "hidden") flush();
});

document.addEventListener(
    "focusin",
    (event) =>
        passkeyDebug("focusin", {
            target: describeElement(event.composedPath()[0] ?? null),
            active: deepActiveElement(),
        }),
    true,
);

document.addEventListener(
    "focusout",
    (event) =>
        passkeyDebug("focusout", { target: describeElement(event.composedPath()[0] ?? null) }),
    true,
);
