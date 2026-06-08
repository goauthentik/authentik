import { applyCustomElementsGetNamePolyfill } from "./custom-elements-get-name.js";

import { describe, expect, it, vi } from "vitest";

/**
 * Build a minimal `CustomElementRegistry`-shaped object suitable for driving
 * the polyfill in a Node environment. `getName` is omitted to simulate older
 * WebKit; `defined` collects the args that reach the underlying `define`.
 */
function makeFakeRegistry(): {
    registry: CustomElementRegistry;
    defined: Array<[string, CustomElementConstructor, ElementDefinitionOptions | undefined]>;
} {
    const defined: Array<[string, CustomElementConstructor, ElementDefinitionOptions | undefined]> =
        [];

    const registry = {
        define: vi.fn((name: string, ctor: CustomElementConstructor, options?) => {
            defined.push([name, ctor, options]);
        }),
        get: vi.fn(),
        whenDefined: vi.fn(),
        upgrade: vi.fn(),
    } as unknown as CustomElementRegistry;

    return { registry, defined };
}

describe("applyCustomElementsGetNamePolyfill", () => {
    it("installs getName when the registry lacks it", () => {
        const { registry } = makeFakeRegistry();

        expect(typeof registry.getName).toBe("undefined");
        applyCustomElementsGetNamePolyfill(registry);
        expect(typeof registry.getName).toBe("function");
    });

    it("returns the registered tag name for a constructor defined after install", () => {
        const { registry } = makeFakeRegistry();
        applyCustomElementsGetNamePolyfill(registry);
        const Ctor = class {} as unknown as CustomElementConstructor;

        registry.define("ak-test-element", Ctor);

        expect(registry.getName(Ctor)).toBe("ak-test-element");
    });

    it("forwards the define call to the original implementation with all arguments", () => {
        const { registry, defined } = makeFakeRegistry();
        applyCustomElementsGetNamePolyfill(registry);
        const Ctor = class {} as unknown as CustomElementConstructor;
        const options = { extends: "button" };

        registry.define("ak-extends-button", Ctor, options);

        expect(defined).toHaveLength(1);
        expect(defined[0]?.[0]).toBe("ak-extends-button");
        expect(defined[0]?.[1]).toBe(Ctor);
        expect(defined[0]?.[2]).toBe(options);
    });

    it("returns null for a constructor that was never registered", () => {
        const { registry } = makeFakeRegistry();
        applyCustomElementsGetNamePolyfill(registry);
        const Unregistered = class {} as unknown as CustomElementConstructor;

        expect(registry.getName(Unregistered)).toBeNull();
    });

    it("does nothing when the registry already implements getName natively", () => {
        const nativeGetName = vi.fn(() => "native-tag");
        const nativeDefine = vi.fn();
        const registry = {
            define: nativeDefine,
            getName: nativeGetName,
            get: vi.fn(),
            whenDefined: vi.fn(),
            upgrade: vi.fn(),
        } as unknown as CustomElementRegistry;

        applyCustomElementsGetNamePolyfill(registry);

        expect(registry.getName).toBe(nativeGetName);
        expect(registry.define).toBe(nativeDefine);
    });
});
