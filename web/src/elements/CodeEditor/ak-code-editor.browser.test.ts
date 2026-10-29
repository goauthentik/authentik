import "#elements/CodeEditor/ak-code-editor";
import { CodeEditor } from "#elements/CodeEditor/ak-code-editor";

import { afterEach, describe, expect, it, vi } from "vitest";
import { userEvent } from "vitest/browser";

import { html, render } from "lit";

const mounted = new Set<HTMLElement>();

/**
 * Render the editor inside a form, the way the admin forms do.
 */
function mount(template: unknown) {
    const form = document.body.appendChild(document.createElement("form"));
    mounted.add(form);

    render(template, form);

    return { form, element: form.querySelector<CodeEditor>("ak-code-editor")! };
}

/**
 * Wait for the lazily imported editor, then place the cursor at the end of the first line.
 */
async function focusEditor(element: CodeEditor) {
    // Vite's dev server transforms Monaco's modules on first import, which takes seconds.
    await vi.waitFor(() => expect(element.shadowRoot?.querySelector(".view-lines")).toBeTruthy(), {
        timeout: 15_000,
    });

    await userEvent.click(element.shadowRoot!.querySelector(".view-lines")!);
    await userEvent.keyboard("{End}");
}

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-code-editor", () => {
    it("submits the value set on the element before the editor loads", () => {
        const { form, element } = mount(
            html`<ak-code-editor name="attributes" mode="yaml" value="a: 1"></ak-code-editor>`,
        );

        expect(new FormData(form).get("attributes")).toBe("a: 1");
        expect(element.toJSON()).toStrictEqual({ a: 1 });
    });

    it("creates the editor once a collapsed group is opened", async () => {
        // With the module already loaded, an editor created on connect would render right away.
        await import("#elements/CodeEditor/editor");

        const { form, element } = mount(
            html`<details>
                <summary>Advanced settings</summary>
                <ak-code-editor mode="yaml" raw value="a: 1"></ak-code-editor>
            </details>`,
        );

        await new Promise((resolve) => setTimeout(resolve, 500));

        expect(element.shadowRoot?.querySelector(".monaco-editor")).toBeNull();

        form.querySelector("details")!.open = true;

        await focusEditor(element);
        await userEvent.keyboard("0");

        expect(element.value).toBe("a: 10");
    });

    it("follows typing", async () => {
        const { form, element } = mount(
            html`<ak-code-editor
                name="expression"
                mode="python"
                raw
                value="x = 1"
            ></ak-code-editor>`,
        );

        const onChange = vi.fn();
        element.addEventListener("change", onChange);

        await focusEditor(element);
        await userEvent.keyboard("0");

        expect(element.value).toBe("x = 10");
        expect(new FormData(form).get("expression")).toBe("x = 10");
        expect(onChange).toHaveBeenCalled();
    });

    it("ignores typing when read-only", async () => {
        const { element } = mount(
            html`<ak-code-editor mode="yaml" raw readonly value="a: 1"></ak-code-editor>`,
        );

        await focusEditor(element);
        await userEvent.keyboard("0");

        expect(element.value).toBe("a: 1");
    });

    it("cuts and pastes with the keyboard", async () => {
        const { element } = mount(
            html`<ak-code-editor mode="yaml" raw value="a: 1"></ak-code-editor>`,
        );

        await focusEditor(element);
        await userEvent.keyboard("{Shift>}{Home}{/Shift}{Control>}x{/Control}");

        expect(element.value).toBe("");

        await userEvent.keyboard("{Control>}v{/Control}{Control>}v{/Control}");

        expect(element.value).toBe("a: 1a: 1");
    });
});
