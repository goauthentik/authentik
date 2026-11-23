import { additionalAcceptedOriginsField } from "./utils.js";

import { serializeForm } from "#elements/forms/serialization";

import { afterEach, expect, it, vi } from "vitest";

import { render } from "lit";

const containers: HTMLElement[] = [];

afterEach(() => {
    containers.forEach((container) => container.remove());
    containers.length = 0;
});

it.each(["additionalAcceptedOrigins", "webauthnAdditionalAcceptedOrigins"])(
    "serializes edits, additions, and removal of all %s entries",
    async (name) => {
        const container = document.body.appendChild(document.createElement("div"));
        containers.push(container);
        render(additionalAcceptedOriginsField(name, ["https://login.example.com"]), container);
        const field = container.querySelector("ak-form-element-horizontal")!;
        const array = container.querySelector("ak-array-input")!;
        const inputs = () => array.renderRoot.querySelectorAll<HTMLInputElement>("input");
        const value = () => serializeForm<Record<string, string[]>>([field])[name];

        await vi.waitFor(() => expect(inputs()).toHaveLength(1));
        expect(value()).toEqual(["https://login.example.com"]);

        const origin = "android:apk-key-hash:" + "A".repeat(43);
        inputs()[0].value = origin;
        inputs()[0].dispatchEvent(new InputEvent("input", { bubbles: true }));
        inputs()[0].dispatchEvent(new Event("change", { bubbles: true }));
        await vi.waitFor(() => expect(value()).toEqual([origin]));

        array.renderRoot.querySelector<HTMLButtonElement>("button.pf-m-link")!.click();
        await vi.waitFor(() => expect(inputs()).toHaveLength(2));
        inputs()[1].value = "https://other.example.com";
        inputs()[1].dispatchEvent(new InputEvent("input", { bubbles: true }));
        inputs()[1].dispatchEvent(new Event("change", { bubbles: true }));
        await vi.waitFor(() => expect(value()).toEqual([origin, "https://other.example.com"]));

        for (const count of [1, 0]) {
            array.renderRoot.querySelector<HTMLButtonElement>("button.pf-m-control")!.click();
            await vi.waitFor(() => expect(inputs()).toHaveLength(count));
        }

        expect(value()).toEqual([]);
    },
);
