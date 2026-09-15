import "#components/ak-secret-search-input";

import { AKFormSubmittedEvent } from "#elements/forms/events";
import { serializeForm } from "#elements/forms/serialization";

import { Secret, SecretsApi, SecretTypeEnum } from "@goauthentik/api";

import { afterEach, expect, test, vi } from "vitest";

const secret: Secret = { pk: "secret-id", name: "Created secret", type: SecretTypeEnum.Text };

afterEach(() => {
    document
        .querySelectorAll("ak-secret-search-input, dialog")
        .forEach((element) => element.remove());
    vi.restoreAllMocks();
});

test("selects a newly created secret even when the dropdown was filtered", async () => {
    vi.spyOn(SecretsApi.prototype, "secretsSecretsList").mockImplementation(
        async ({ search } = {}) => ({
            results: search ? [] : [secret],
        }),
    );
    const picker = document.createElement("ak-secret-search-input");
    document.body.append(picker);
    await picker.updateComplete;
    const select = picker.querySelector("ak-search-select")!;
    select.query = "no match";
    await select.updateData();

    picker.querySelector<HTMLButtonElement>("button")!.click();
    await vi.waitFor(() => expect(document.querySelector("ak-secret-form")).not.toBeNull());
    document.querySelector("ak-secret-form")!.dispatchEvent(new AKFormSubmittedEvent(secret));

    await vi.waitFor(() => expect(select.toForm()).toBe(secret.pk));
    expect(picker.value).toBe(secret.pk);
});

test("loads a selected secret outside the first page", async () => {
    vi.spyOn(SecretsApi.prototype, "secretsSecretsList").mockResolvedValue({ results: [] });
    const retrieve = vi
        .spyOn(SecretsApi.prototype, "secretsSecretsRetrieve")
        .mockResolvedValue(secret);
    const picker = document.createElement("ak-secret-search-input");
    picker.name = "secret";
    picker.value = secret.pk;
    document.body.append(picker);
    await picker.updateComplete;
    const select = picker.querySelector("ak-search-select")!;

    await vi.waitFor(() => expect(select.toForm()).toBe(secret.pk));
    expect(retrieve).toHaveBeenCalledWith({ secretUuid: secret.pk });
});

test.each([false, true])(
    "preserves the selected secret when lookup fails (blankable=%s)",
    async (blankable) => {
        vi.spyOn(SecretsApi.prototype, "secretsSecretsList").mockResolvedValue({ results: [] });
        vi.spyOn(SecretsApi.prototype, "secretsSecretsRetrieve").mockRejectedValue(
            new Error("Unavailable"),
        );
        const picker = document.createElement("ak-secret-search-input");
        picker.name = "secret";
        picker.value = secret.pk;
        picker.blankable = blankable;
        document.body.append(picker);
        await picker.updateComplete;
        const select = picker.querySelector("ak-search-select")!;

        await vi.waitFor(() =>
            expect(select.shadowRoot?.textContent).toContain("Failed to fetch objects"),
        );
        expect(() =>
            serializeForm([picker.querySelector("ak-form-element-horizontal")!]),
        ).toThrow();
        expect(picker.value).toBe(secret.pk);
    },
);
