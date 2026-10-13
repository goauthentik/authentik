import "#components/ak-secret-search-input";
import { AKRefreshEvent } from "#common/events";

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

test("selects a newly created secret", async () => {
    const list = vi
        .spyOn(SecretsApi.prototype, "secretsSecretsList")
        .mockResolvedValue({ results: [] });

    const picker = document.createElement("ak-secret-search-input");
    document.body.append(picker);
    await picker.updateComplete;
    const select = picker.querySelector("ak-search-select")!;
    await vi.waitFor(() => expect(list).toHaveBeenCalled());
    list.mockResolvedValue({ results: [secret] });

    picker.querySelector<HTMLButtonElement>("button")!.click();
    await vi.waitFor(() => expect(document.querySelector("ak-secret-form")).not.toBeNull());
    document.querySelector("ak-secret-form")!.dispatchEvent(new AKFormSubmittedEvent(secret));

    await vi.waitFor(() => expect(select.value).toBe(secret.pk));
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

    await vi.waitFor(() => expect(select.value).toBe(secret.pk));
    expect(retrieve).toHaveBeenCalledWith({ secretUuid: secret.pk });
});

test("keeps a selected secret the user can't view", async () => {
    vi.spyOn(SecretsApi.prototype, "secretsSecretsList").mockResolvedValue({ results: [] });

    vi.spyOn(SecretsApi.prototype, "secretsSecretsRetrieve").mockRejectedValue(
        new Error("Not found"),
    );

    const picker = document.createElement("ak-secret-search-input");
    picker.name = "secret";
    picker.value = secret.pk;
    document.body.append(picker);
    const select = picker.querySelector("ak-search-select")!;

    await vi.waitFor(() => expect(select.value).toBe(secret.pk));

    expect(serializeForm([picker.querySelector("ak-form-element-horizontal")!])).toEqual({
        secret: secret.pk,
    });

    expect(picker.querySelectorAll("button")).toHaveLength(1);
});

test("refreshes from the picker don't reload the surrounding form", async () => {
    vi.spyOn(SecretsApi.prototype, "secretsSecretsList").mockResolvedValue({ results: [] });
    const picker = document.createElement("ak-secret-search-input");
    document.body.append(picker);
    await picker.updateComplete;
    const refresh = vi.fn();
    document.body.addEventListener(AKRefreshEvent.eventName, refresh);

    picker.querySelector("button")!.dispatchEvent(new AKRefreshEvent());

    document.body.removeEventListener(AKRefreshEvent.eventName, refresh);
    expect(refresh).not.toHaveBeenCalled();
});

test("filters scalar secrets and restricts inline creation", async () => {
    const list = vi
        .spyOn(SecretsApi.prototype, "secretsSecretsList")
        .mockResolvedValue({ results: [] });

    const picker = document.createElement("ak-secret-search-input");
    document.body.append(picker);
    await vi.waitFor(() => expect(list).toHaveBeenCalled());
    expect(list.mock.calls[0][0]).toMatchObject({ typeIn: [SecretTypeEnum.Text] });
    picker.querySelector<HTMLButtonElement>("button")!.click();
    await vi.waitFor(() => expect(document.querySelector("ak-secret-form")).toBeTruthy());
    expect(document.querySelector("ak-secret-form")!.types).toEqual([SecretTypeEnum.Text]);
});
