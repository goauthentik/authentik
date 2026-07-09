import { DOMEventHandlerNames, kebabCase, resolveEventName } from "@goauthentik/lit-jsx";

import { describe, expect, it } from "vitest";

describe("kebabCase", () => {
    it.each([
        ["AkChange", "ak-change"],
        ["AKChange", "ak-change"],
        ["AkSearchSelectInput", "ak-search-select-input"],
        ["MyEvent", "my-event"],
        ["Change", "change"],
    ])("converts %s to %s", (input, expected) => {
        expect(kebabCase(input)).toBe(expected);
    });
});

describe("resolveEventName", () => {
    it("resolves canonical camelCase DOM handler names", () => {
        expect(resolveEventName("onClick")).toBe("click");
        expect(resolveEventName("onDblClick")).toBe("dblclick");
        expect(resolveEventName("onMouseDown")).toBe("mousedown");
        expect(resolveEventName("onCanPlayThrough")).toBe("canplaythrough");
    });

    it("resolves non-canonical casings of known DOM events by lowercasing", () => {
        expect(resolveEventName("onDblclick")).toBe("dblclick");
        expect(resolveEventName("onMousedown")).toBe("mousedown");
    });

    it("kebab-cases unknown (custom) event names", () => {
        expect(resolveEventName("onAkChange")).toBe("ak-change");
        expect(resolveEventName("onAKChange")).toBe("ak-change");
        expect(resolveEventName("onAkSearchSelectInput")).toBe("ak-search-select-input");
    });

    it("returns null for props that are not event handlers", () => {
        expect(resolveEventName("onclick")).toBeNull();
        expect(resolveEventName("once")).toBeNull();
        expect(resolveEventName("on")).toBeNull();
        expect(resolveEventName("label")).toBeNull();
    });
});

describe("DOMEventHandlerNames", () => {
    it("maps every handler to a lowercase event name", () => {
        for (const [handler, event] of Object.entries(DOMEventHandlerNames)) {
            expect(handler).toMatch(/^on[A-Z]/);
            expect(event).toBe(event.toLowerCase());
        }
    });
});
