import { createElementTemplate, mapJSXProps } from "@goauthentik/lit-jsx";

import { render } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { createRef, ref } from "lit/directives/ref.js";

import { describe, expect, it } from "vitest";

import { AkTestBadge } from "../fixtures/elements.js";

function mount(template: unknown): HTMLDivElement {
    const host = document.createElement("div");
    document.body.appendChild(host);
    render(template, host);
    return host;
}

function renderProps(
    tagName: string,
    props: Record<string, unknown>,
    ElementConstructor?: typeof AkTestBadge,
) {
    return createElementTemplate(tagName, mapJSXProps(props, ElementConstructor));
}

describe("createElementTemplate", () => {
    it("renders attributes, class, and children on an intrinsic element", () => {
        const host = mount(
            renderProps("section", { "id": "hello", "class": "a b", "children": "Hi", "data-x": "1" }),
        );
        const section = host.querySelector("section#hello");

        expect(section).not.toBeNull();
        expect(section!.className).toBe("a b");
        expect(section!.getAttribute("data-x")).toBe("1");
        expect(section!.textContent?.trim()).toBe("Hi");
    });

    it("omits the class attribute when no class value is given", () => {
        const host = mount(renderProps("div", {}));
        expect(host.querySelector("div")!.hasAttribute("class")).toBe(false);
    });

    it("supports the classMap directive for class", () => {
        const host = mount(renderProps("div", { class: classMap({ on: true, off: false }) }));
        expect(host.querySelector("div")!.className.trim()).toBe("on");
    });

    it("applies style objects via styleMap and style strings directly", () => {
        const fromObject = mount(renderProps("div", { style: { color: "rgb(255, 0, 0)" } }));
        const fromString = mount(renderProps("div", { style: "color: rgb(0, 0, 255)" }));

        expect((fromObject.querySelector("div") as HTMLElement).style.color).toBe("rgb(255, 0, 0)");
        expect((fromString.querySelector("div") as HTMLElement).style.color).toBe("rgb(0, 0, 255)");
    });

    it("wires the ref directive", () => {
        const divRef = createRef<HTMLDivElement>();
        const host = mount(renderProps("div", { ref: divRef }));
        expect(divRef.value).toBe(host.querySelector("div"));
    });

    it("renders void elements without children or a closing tag", () => {
        const host = mount(renderProps("input", { type: "text", value: "typed" }));
        const input = host.querySelector("input")!;

        expect(input.type).toBe("text");
        expect(input.value).toBe("typed");
    });

    it("throws when a void element is given children", () => {
        expect(() => renderProps("input", { children: "nope" })).toThrow(TypeError);
    });

    it("applies declared reactive properties to a custom element", async () => {
        const host = mount(
            renderProps(
                "ak-test-badge",
                { label: "hi", active: true, level: "warn", items: ["a", "b"] },
                AkTestBadge,
            ),
        );
        const badge = host.querySelector("ak-test-badge")!;
        await badge.updateComplete;

        expect(badge.getAttribute("label")).toBe("hi");
        expect(badge.hasAttribute("active")).toBe(true);
        expect(badge.getAttribute("data-level")).toBe("warn");
        expect(badge.items).toEqual(["a", "b"]);
        expect(badge.shadowRoot!.textContent).toContain("hi:2");
    });

    it("updates the same element on re-render instead of replacing it", async () => {
        const host = document.createElement("div");
        document.body.appendChild(host);

        render(renderProps("ak-test-badge", { label: "one", items: [] }, AkTestBadge), host);
        const first = host.querySelector("ak-test-badge")!;
        await first.updateComplete;

        render(renderProps("ak-test-badge", { label: "two", items: ["a"] }, AkTestBadge), host);
        const second = host.querySelector("ak-test-badge")!;
        await second.updateComplete;

        expect(second).toBe(first);
        expect(second.label).toBe("two");
        expect(second.shadowRoot!.textContent).toContain("two:1");
    });

    it("removes bindings that disappear between renders", async () => {
        const host = document.createElement("div");
        document.body.appendChild(host);

        render(renderProps("div", { "data-x": "1" }), host);
        expect(host.querySelector("div")!.getAttribute("data-x")).toBe("1");

        render(renderProps("div", {}), host);
        expect(host.querySelector("div")!.hasAttribute("data-x")).toBe(false);
    });
});
