/** @jsxImportSource @goauthentik/lit-jsx */

import { renderVariants } from "./utils.js";

import { test } from "vitest";

import { html } from "@lit-labs/ssr";
import { styleMap } from "lit/directives/style-map.js";

test("Simple static markup can be rendered", async ({ expect }) => {
    const [result, comparision] = await renderVariants(
        // @ts-ignore - testing
        <div>Hello World</div>,
        html`<div>Hello World</div>`,
    );

    expect(result, "JSX element serialized to a matching string").toBe(comparision);
});

test("`className` is rendered to the correct attribute", async ({ expect }) => {
    const [result, comparision] = await renderVariants(
        // @ts-ignore - testing
        <p className="one two">Hello World</p>,
        html`<p class="one two">Hello World</p>`,
    );

    expect(result, "`className` is rendered to the correct attribute").toBe(comparision);
});

test("`style` is rendered to the correct attribute", async ({ expect }) => {
    const [result, comparision] = await renderVariants(
        // @ts-ignore - testing
        <p style={{ color: "red", fontSize: "12px" }}>Hello World</p>,
        html`<p style=${styleMap({ color: "red", fontSize: "12px" })}>Hello World</p>`,
    );

    expect(result, "style is rendered to the correct attribute").toBe(comparision);
});

test("`style` is rendered to the correct attribute", async ({ expect }) => {
    const [result, comparision] = await renderVariants(
        // @ts-ignore - testing
        <p style={{ color: "red", fontSize: "12px" }}>Hello World</p>,
        html`<p style=${styleMap({ color: "red", fontSize: "12px" })}>Hello World</p>`,
    );

    expect(result, "style is rendered to the correct attribute").toBe(comparision);
});
