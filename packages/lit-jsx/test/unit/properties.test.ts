import { mapJSXProps } from "@goauthentik/lit-jsx";

import { nothing, type PropertyDeclaration } from "lit";

import { describe, expect, it } from "vitest";

/**
 * A stand-in for a LitElement constructor: `mapJSXProps` only reads
 * `elementProperties`, `observedAttributes`, and `prototype`, so unit tests
 * need no DOM.
 */
const FakeBadgeElement = {
    elementProperties: new Map<PropertyKey, PropertyDeclaration>([
        ["label", { type: String, attribute: true }],
        ["active", { type: Boolean, attribute: true }],
        ["level", { type: String, attribute: "data-level" }],
        ["items", { attribute: false }],
        ["count", { type: Number, attribute: true }],
    ]),
    observedAttributes: ["label", "active", "data-level", "count"],
    prototype: {},
};

describe("mapJSXProps", () => {
    describe("special props", () => {
        it("captures children, class, style, and ref out of the bindings", () => {
            const onRef = () => {};
            const mapped = mapJSXProps({
                children: "text",
                class: ["a", { b: true }],
                style: { color: "red" },
                ref: onRef,
            });

            expect(mapped.children).toBe("text");
            expect(mapped.classValue).toBe("a b");
            expect(mapped.styleValue).toEqual({ color: "red" });
            expect(mapped.refValue).toBe(onRef);
            expect(mapped.bindings).toEqual({});
        });

        it("accepts className as an alias for class", () => {
            expect(mapJSXProps({ className: "a" }).classValue).toBe("a");
        });

        it("normalizes an empty class to undefined", () => {
            expect(mapJSXProps({ class: [null, false] }).classValue).toBeUndefined();
        });

        it("maps htmlFor to the for attribute", () => {
            expect(mapJSXProps({ htmlFor: "field-1" }).bindings).toEqual({ "for": "field-1" });
        });

        it("ignores key", () => {
            expect(mapJSXProps({ key: 3 }).bindings).toEqual({});
        });

        it("coerces lit's nothing sentinel to undefined so spread removes the binding", () => {
            // `nothing` is only meaningful to template parts; through the
            // spread directive it would be stringified into the attribute.
            expect(mapJSXProps({ "data-x": nothing }).bindings).toEqual({ "data-x": undefined });
        });
    });

    describe("event props", () => {
        it("binds DOM and custom events with the @ sigil", () => {
            const onClick = () => {};
            const onAkChange = () => {};
            const mapped = mapJSXProps({ onClick, onAkChange });

            expect(mapped.bindings).toEqual({
                "@click": onClick,
                "@ak-change": onAkChange,
            });
        });
    });

    describe("declared reactive properties", () => {
        it("resolves prefixes from the element's property declarations", () => {
            const items = ["a"];
            const mapped = mapJSXProps(
                { label: "hi", active: true, items, count: 2 },
                FakeBadgeElement,
            );

            expect(mapped.bindings).toEqual({
                "label": "hi",
                "?active": true,
                ".items": items,
                ".count": 2,
            });
        });

        it("honors custom attribute names from the declaration", () => {
            const mapped = mapJSXProps({ level: "warning" }, FakeBadgeElement);
            expect(mapped.bindings).toEqual({ "data-level": "warning" });
        });

        it("treats a declaration without an attribute key as an attribute (lit default)", () => {
            const BareDeclarationElement = {
                elementProperties: new Map<PropertyKey, PropertyDeclaration>([
                    ["label", { type: String }],
                    ["active", { type: Boolean }],
                    ["items", { attribute: false }],
                ]),
                prototype: {},
            };

            const mapped = mapJSXProps({ label: "hi", active: true, items: [] }, BareDeclarationElement);

            expect(mapped.bindings).toEqual({
                "label": "hi",
                "?active": true,
                ".items": [],
            });
        });
    });

    describe("fallback heuristics (native elements and undeclared props)", () => {
        it("binds value, checked, and selected as properties", () => {
            const mapped = mapJSXProps({ value: "text", checked: true, selected: false });
            expect(mapped.bindings).toEqual({
                ".value": "text",
                ".checked": true,
                ".selected": false,
            });
        });

        it("binds booleans as boolean attributes", () => {
            expect(mapJSXProps({ disabled: true }).bindings).toEqual({ "?disabled": true });
        });

        it("binds objects and functions as properties", () => {
            const callback = () => {};
            const options = { a: 1 };
            const mapped = mapJSXProps({ callback, options });
            expect(mapped.bindings).toEqual({ ".callback": callback, ".options": options });
        });

        it("binds primitives as attributes", () => {
            const mapped = mapJSXProps({ id: "x", tabindex: 0, title: "t" });
            expect(mapped.bindings).toEqual({ "id": "x", "tabindex": 0, "title": "t" });
        });
    });
});
