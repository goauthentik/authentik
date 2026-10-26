import "#elements/ToggleGroup";
import "#elements/forms/HorizontalFormElement";
import { serializeForm } from "#elements/forms/serialization";
import type { ToggleGroup } from "#elements/ToggleGroup";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { html, render, TemplateResult } from "lit";

describe("ak-toggle-group", () => {
    let host: HTMLDivElement;

    beforeEach(() => {
        host = document.createElement("div");
        document.body.append(host);
    });

    afterEach(() => host.remove());

    const options = () => html`<option value="a">A</option>
        <option value="b">B</option>`;

    async function mount(template: TemplateResult) {
        render(template, host);
        const group = host.querySelector("ak-toggle-group")!;
        await group.updateComplete;

        return group;
    }

    function click(group: ToggleGroup, index: number) {
        group.renderRoot.querySelectorAll("button")[index].click();
    }

    it("Sets the value BEFORE ak-toggle fires", async () => {
        const group = await mount(html`<ak-toggle-group value="a">${options()}</ak-toggle-group>`);
        let seen = "";
        group.addEventListener("ak-toggle", () => (seen = group.value));
        click(group, 1);
        expect(seen).toBe("b");
    });

    it("can serialize inside ak-form-element-horizontal", async () => {
        render(
            html`<ak-form-element-horizontal label="Mode" name="mode">
                <ak-toggle-group value="a">${options()}</ak-toggle-group>
            </ak-form-element-horizontal>`,
            host,
        );

        const akfeh = host.querySelector("ak-form-element-horizontal")!;
        await akfeh.updateComplete;
        const group = host.querySelector("ak-toggle-group")!;
        await group.updateComplete;
        click(group, 1);
        expect(serializeForm([akfeh])).toEqual({ mode: "b" });
    });
});
