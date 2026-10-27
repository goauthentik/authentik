import "#elements/ak-checkbox-group/ak-checkbox-group";
import { CheckboxGroup } from "#elements/ak-checkbox-group/ak-checkbox-group";

import { afterEach, describe, expect, it } from "vitest";

import { html, render } from "lit";

const options = [
    ["authorization_code", "Authorization code"],
    ["refresh_token", "Refresh token"],
    ["password", "Password"],
] as const;

const mounted = new Set<HTMLElement>();

interface MountInit {
    required?: boolean;
}

/**
 * Render the checkbox group inside a form from a host template, the way a form does.
 */
async function mount(value: string[], init: MountInit = {}) {
    const form = document.body.appendChild(document.createElement("form"));
    mounted.add(form);

    const renderHost = async (nextValue: string[]) => {
        render(
            html`<ak-checkbox-group
                name="grantTypes"
                ?required=${init.required}
                .options=${options}
                .value=${nextValue}
            ></ak-checkbox-group>`,
            form,
        );

        const element = form.querySelector<CheckboxGroup>("ak-checkbox-group")!;
        await element.updateComplete;

        return element;
    };

    return { form, element: await renderHost(value), renderHost };
}

function checkbox(element: CheckboxGroup, name: string) {
    return element.renderRoot.querySelector<HTMLInputElement>(`input[name="${name}"]`)!;
}

async function toggle(element: CheckboxGroup, name: string) {
    checkbox(element, name).click();
    await element.updateComplete;
}

afterEach(() => {
    mounted.forEach((container) => container.remove());
    mounted.clear();
});

describe("ak-checkbox-group: host value", () => {
    it("checks the options named in value", async () => {
        const { element } = await mount(["refresh_token"]);

        expect(checkbox(element, "refresh_token").checked).toBe(true);
        expect(checkbox(element, "password").checked).toBe(false);
        expect(element.toJSON()).toStrictEqual(["refresh_token"]);
    });

    it("keeps the user's choices when the host re-renders with the same names", async () => {
        const { element, renderHost } = await mount(["refresh_token"]);

        await toggle(element, "password");
        await renderHost(["refresh_token"]);

        expect(element.toJSON()).toStrictEqual(["refresh_token", "password"]);
        expect(checkbox(element, "password").checked).toBe(true);
    });

    it("replaces the user's choices when the host passes different names", async () => {
        const { element, renderHost } = await mount(["refresh_token"]);

        await toggle(element, "password");
        await renderHost(["authorization_code"]);

        expect(element.toJSON()).toStrictEqual(["authorization_code"]);
        expect(checkbox(element, "password").checked).toBe(false);
    });
});

describe("ak-checkbox-group: events", () => {
    it("dispatches one change and one input event with the selection", async () => {
        const { form, element } = await mount([]);
        const seen: string[] = [];

        form.addEventListener("change", (event) =>
            seen.push(`change:${(event as CustomEvent<string[]>).detail.join(",")}`),
        );

        form.addEventListener("input", (event) =>
            seen.push(`input:${(event as CustomEvent<string[]>).detail.join(",")}`),
        );

        await toggle(element, "password");

        expect(seen).toStrictEqual(["change:password", "input:password"]);
    });
});

describe("ak-checkbox-group: form association", () => {
    it("submits one entry per chosen option", async () => {
        const { form, element } = await mount(["refresh_token"]);

        await toggle(element, "password");

        expect(Array.from(form.elements)).toContain(element);

        expect(new FormData(form).getAll("grantTypes")).toStrictEqual([
            "refresh_token",
            "password",
        ]);
    });

    it("restores the host's value when the form resets", async () => {
        const { form, element } = await mount(["refresh_token"]);

        await toggle(element, "refresh_token");
        await toggle(element, "password");
        form.reset();
        await element.updateComplete;

        expect(element.toJSON()).toStrictEqual(["refresh_token"]);
        expect(checkbox(element, "refresh_token").checked).toBe(true);
        expect(checkbox(element, "password").checked).toBe(false);
    });

    it("is missing a value when required and nothing is chosen", async () => {
        const { element } = await mount([], { required: true });

        expect(element.validity.valueMissing).toBe(true);

        await toggle(element, "password");

        expect(element.checkValidity()).toBe(true);
    });

    it("is valid when not required and nothing is chosen", async () => {
        const { element } = await mount([]);

        expect(element.checkValidity()).toBe(true);
    });
});
