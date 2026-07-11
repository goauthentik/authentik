import type { FC } from "@goauthentik/lit-jsx";

import { html, render } from "lit";

import { describe, expect, it, vi } from "vitest";

import { AkTestBadge, AkTestUnregistered } from "../fixtures/elements.js";

function mount(template: unknown): HTMLDivElement {
    const host = document.createElement("div");
    document.body.appendChild(host);
    render(template, host);
    return host;
}

describe("jsx runtime", () => {
    it("renders intrinsic elements with children", () => {
        const host = mount(
            <section id="root">
                <p class="lead">Hello</p>
            </section>,
        );

        expect(host.querySelector("section#root > p.lead")?.textContent).toBe("Hello");
    });

    it("renders a registered custom element class as a tag", async () => {
        // @ts-expect-error - TODO(task-8): class-as-JSX-tag prop typing lands in Task 8
        const host = mount(<AkTestBadge label="hi" active items={["a", "b"]} />);
        const badge = host.querySelector("ak-test-badge")!;
        await badge.updateComplete;

        expect(badge.getAttribute("label")).toBe("hi");
        expect(badge.hasAttribute("active")).toBe(true);
        expect(badge.items).toEqual(["a", "b"]);
    });

    it("resolves elementProperties for intrinsic custom-element tag names too", async () => {
        const host = mount(<ak-test-badge label="via-tag" items={["a"]} />);
        const badge = host.querySelector("ak-test-badge")!;
        await badge.updateComplete;

        expect(badge.items).toEqual(["a"]);
    });

    it("throws a descriptive error for unregistered custom element classes", () => {
        expect(() => mount(<AkTestUnregistered />)).toThrow(/AkTestUnregistered.*not registered/);
    });

    it("calls function components with children in props", () => {
        const Wrapper: FC<{ title: string }> = ({ title, children }) => (
            <div class="wrapper" title={title}>
                {children}
            </div>
        );

        const host = mount(
            <Wrapper title="t">
                <em>inner</em>
            </Wrapper>,
        );

        expect(host.querySelector("div.wrapper[title='t'] > em")?.textContent).toBe("inner");
    });

    it("renders fragments", () => {
        const host = mount(
            <>
                <i>a</i>
                <i>b</i>
            </>,
        );

        expect(host.querySelectorAll("i")).toHaveLength(2);
    });

    it("dispatches events to on* handlers, including custom events", async () => {
        const onClick = vi.fn();
        const onAkChange = vi.fn();

        const host = mount(
            <div>
                <button onClick={onClick}>go</button>
                {
                    // @ts-expect-error - TODO(task-8): class-as-JSX-tag prop typing lands in Task 8
                    <AkTestBadge label="evt" onAkChange={onAkChange} />
                }
            </div>,
        );

        const badge = host.querySelector("ak-test-badge")!;
        await badge.updateComplete;

        host.querySelector("button")!.click();
        badge.emitChange();

        expect(onClick).toHaveBeenCalledTimes(1);
        expect(onAkChange).toHaveBeenCalledTimes(1);
    });

    it("interops with html`` in both directions", () => {
        const inner = <span id="jsx-inner">jsx</span>;
        const host = mount(html`<div id="lit-outer">${inner}${(<b>bold</b>)}</div>`);

        expect(host.querySelector("#lit-outer > #jsx-inner")?.textContent).toBe("jsx");
        expect(host.querySelector("#lit-outer > b")?.textContent).toBe("bold");

        const litInner = html`<u>lit</u>`;
        const jsxOuter = mount(<div id="jsx-outer">{litInner}</div>);
        expect(jsxOuter.querySelector("#jsx-outer > u")?.textContent).toBe("lit");
    });

    it("renders conditional and list children", () => {
        const items = ["a", "b", "c"];
        const host = mount(
            <ul>
                {items.map((item) => (
                    <li>{item}</li>
                ))}
                {false}
                {null}
            </ul>,
        );

        expect(host.querySelectorAll("li")).toHaveLength(3);
        expect(host.querySelector("ul")!.textContent).not.toContain("false");
    });
});
