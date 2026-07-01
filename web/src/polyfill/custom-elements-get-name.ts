/**
 * @file Polyfill for `CustomElementRegistry.getName()` on older WebKit.
 *
 * `getName()` is the reverse of `customElements.get()`: given a custom-element
 * constructor, it returns the tag name it was registered under (or `null`).
 * It landed in Chrome/Edge 117, Firefox 119, and Safari 17.4 — so iOS 16, the
 * iOS 17.0–17.3 series, and any WebKit WebView pinned below 17.4 reach the
 * authentik flow renderer without it and crash at the first call site.
 *
 * The polyfill keeps a reverse map by wrapping `define()` so that any later
 * registration is recorded; on browsers that already implement `getName()`
 * natively it is a no-op. Because the wrap can only observe registrations made
 * *after* it installs, this module must be imported before any
 * `customElements.define(...)` call — which is what the polyfill entry point
 * guarantees, since it is loaded ahead of every interface bundle in
 * `base/skeleton.html`.
 */

/**
 * Install the `getName()` polyfill on the given registry if it is absent.
 *
 * Exported separately from the side-effect import so that unit tests can drive
 * the polyfill against a fake registry without touching the global one.
 */
export function applyCustomElementsGetNamePolyfill(
    registry: Partial<CustomElementRegistry>,
): asserts registry is CustomElementRegistry {
    if (typeof registry.getName === "function") return;

    if (typeof registry.define !== "function") {
        console.warn(
            "CustomElementRegistry.getName polyfill: registry lacks define() method, cannot install polyfill",
        );

        return;
    }

    const nameByCtor = new WeakMap<CustomElementConstructor, string>();
    const originalDefine = registry.define.bind(registry);

    registry.define = function define(
        name: string,
        ctor: CustomElementConstructor,
        options?: ElementDefinitionOptions,
    ): void {
        nameByCtor.set(ctor, name);

        return originalDefine(name, ctor, options);
    };

    registry.getName = function getName(ctor: CustomElementConstructor): string | null {
        return nameByCtor.get(ctor) ?? null;
    };
}

if (typeof window !== "undefined" && window.customElements) {
    applyCustomElementsGetNamePolyfill(window.customElements);
}
