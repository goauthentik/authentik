import { Form } from "#elements/forms/Form";
import { ModelForm } from "#elements/forms/ModelForm";

import { afterEach, expect, test, vi } from "vitest";

import { html } from "lit";

const fields = () => html`<input name="name" /><input name="file" type="file" />`;

class VisibilityForm extends Form {
    protected override renderForm() {
        return fields();
    }
}

class VisibilityModelForm extends ModelForm {
    protected override renderForm() {
        return fields();
    }
}

customElements.define("ak-visibility-form", VisibilityForm);
customElements.define("ak-visibility-model-form", VisibilityModelForm);

afterEach(() => {
    document
        .querySelectorAll("ak-visibility-form, ak-visibility-model-form")
        .forEach((form) => form.remove());
});

test.each(["ak-visibility-form", "ak-visibility-model-form"])(
    "%s retains text and uploaded files across viewport changes",
    async (tag) => {
        const form = document.createElement(tag) as Form;
        form.style.cssText = "position: fixed; top: -10000px; width: 400px; height: 300px";
        document.body.append(form);
        await form.updateComplete;
        expect(form.shadowRoot!.querySelector("input")).toBeNull();

        form.style.top = "0";
        await vi.waitFor(() => expect(form.shadowRoot!.querySelector("input")).toBeTruthy());
        const name = form.shadowRoot!.querySelector<HTMLInputElement>('[name="name"]')!;
        const file = form.shadowRoot!.querySelector<HTMLInputElement>('[name="file"]')!;
        name.value = "Unsaved name";
        const transfer = new DataTransfer();
        transfer.items.add(new File([new Uint8Array([0, 128, 255])], "secret.bin"));
        file.files = transfer.files;

        form.style.top = "-10000px";
        await vi.waitFor(() => expect(form.visible).toBe(false));
        await form.updateComplete;
        expect(form.shadowRoot!.querySelector('[name="name"]')).toBe(name);
        expect(form.shadowRoot!.querySelector('[name="file"]')).toBe(file);

        form.style.top = "0";
        await vi.waitFor(() => expect(form.visible).toBe(true));
        await form.updateComplete;
        expect(form.shadowRoot!.querySelector('[name="name"]')).toBe(name);
        expect(name.value).toBe("Unsaved name");
        expect(form.shadowRoot!.querySelector('[name="file"]')).toBe(file);
        expect(file.files![0].name).toBe("secret.bin");

        expect(new Uint8Array(await file.files![0].arrayBuffer())).toEqual(
            new Uint8Array([0, 128, 255]),
        );
    },
);
