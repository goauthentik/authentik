import "#flow/components/ak-prompt-showable-password";
import { ShowablePassword } from "#flow/components/ak-prompt-showable-password";
import { mountPromptStage, stagePrompt, unmountPromptStages } from "#flow/tests/prompt-stage";

import { PromptTypeEnum } from "@goauthentik/api";

import { afterEach, describe, expect, it } from "vitest";
import { page, userEvent } from "vitest/browser";

import { html, render } from "lit";

const container = document.createElement("div");

async function mount() {
    document.body.append(container);

    render(
        html`<ak-prompt-showable-password
            fieldid="field-secret"
            fieldkey="secret"
            placeholder="Password"
            required
        ></ak-prompt-showable-password>`,
        container,
    );

    const element = container.querySelector<ShowablePassword>("ak-prompt-showable-password")!;
    await element.updateComplete;

    return {
        element,
        input: element.querySelector("input")!,
        button: element.querySelector("button")!,
    };
}

afterEach(() => {
    render(null, container);
    container.remove();
    unmountPromptStages();
});

describe("ak-prompt-showable-password", () => {
    it("correctly initializes the new showable password's input and button", async () => {
        const { input, button } = await mount();

        expect(input.type).toBe("password");
        expect(input.id).toBe("field-secret");
        expect(input.name).toBe("secret");
        expect(input.placeholder).toBe("Password");
        expect(input.required).toBe(true);
        expect(button.type).toBe("button");
        expect(button.getAttribute("aria-label")).toBe("View password");
    });

    it("does show and hide without losing the input value", async () => {
        const { element, input, button } = await mount();

        await userEvent.fill(input, "oh rocky!");

        button.click();
        await element.updateComplete;

        expect(input.type).toBe("text");
        expect(button.getAttribute("aria-label")).toBe("Hide password");
        expect(input.value).toBe("oh rocky!");

        button.click();
        await element.updateComplete;

        expect(input.type).toBe("password");
        expect(button.getAttribute("aria-label")).toBe("View password");
        expect(input.value).toBe("oh rocky!");
    });

    it("throws an exception when the dev forgets the id or name", () => {
        const element = new ShowablePassword();

        expect(() => element.fieldKeys).toThrow(/fieldId/);

        element.fieldId = "field-secret";

        expect(() => element.fieldKeys).toThrow(/fieldKey/);
    });
});

describe("ak-prompt-showable-password in <ak-stage-prompt>", () => {
    // Copies the form from the Storybook entry: one standard and one viewable password.
    const fields = [
        stagePrompt({ fieldKey: "password", type: PromptTypeEnum.Password, label: "Standard" }),
        stagePrompt({
            fieldKey: "password_viewable",
            type: PromptTypeEnum.PasswordViewable,
            label: "Viewable",
            order: 1,
        }),
    ];

    it("gets the stage's field label", async () => {
        await mountPromptStage(fields);

        await expect.element(page.getByLabelText("Viewable")).toHaveAttribute("type", "password");
    });

    it("submits the value correctly under the prompt's field key when shown or hidden", async () => {
        const { submit } = await mountPromptStage(fields);

        await page.getByLabelText("Standard").fill("plain");
        await page.getByLabelText("Viewable").fill("shown");

        // The toggle is type="button", so clicking it shouldn't submit the form.
        await page.getByRole("button", { name: "View password" }).click();
        expect(submit).not.toHaveBeenCalled();

        await expect.element(page.getByLabelText("Viewable")).toHaveAttribute("type", "text");

        await page.getByRole("button", { name: "Continue" }).click();

        await expect
            .poll(() => submit.mock.calls[0]?.[0])
            .toEqual({
                password: "plain",
                password_viewable: "shown",
            });
    });
});
