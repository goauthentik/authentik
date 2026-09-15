import "#admin/secrets/SecretForm";

import { downloadFile } from "#common/download";

import { SecretValueButton } from "#admin/secrets/SecretValueButton";

import { Secret, SecretsApi, SecretTypeEnum } from "@goauthentik/api";

import { afterEach, expect, test, vi } from "vitest";

import { render } from "lit";

vi.mock("#common/download", () => ({ downloadFile: vi.fn() }));
vi.mock("#elements/messages/MessageContainer", async (importOriginal) => ({
    ...(await importOriginal<object>()),
    showMessage: vi.fn(),
}));

afterEach(() => {
    document
        .querySelectorAll("ak-secret-form, #file-action")
        .forEach((element) => element.remove());
    vi.restoreAllMocks();
});

test("uploading and downloading a file preserves binary content", async () => {
    const secret: Secret = { pk: "file-id", name: "test.bin", type: SecretTypeEnum.File };
    vi.spyOn(SecretsApi.prototype, "secretsSecretsRetrieve").mockResolvedValue(secret);
    const update = vi
        .spyOn(SecretsApi.prototype, "secretsSecretsPartialUpdate")
        .mockResolvedValue(secret);
    const form = document.createElement("ak-secret-form");
    form.instancePk = secret.pk;
    document.body.append(form);
    await vi.waitFor(() =>
        expect(form.shadowRoot?.querySelector('input[type="file"]')).not.toBeNull(),
    );
    const bytes = new Uint8Array([0, 10, 127, 128, 255]);
    const transfer = new DataTransfer();
    transfer.items.add(new File([bytes], secret.name));
    form.shadowRoot!.querySelector<HTMLInputElement>('input[type="file"]')!.files = transfer.files;
    await form.submit(new SubmitEvent("submit"));
    expect(update).toHaveBeenCalledOnce();
    const value = update.mock.calls[0][0].patchedSecretRequest.value!;
    vi.spyOn(SecretsApi.prototype, "secretsSecretsViewValueRetrieve").mockResolvedValue({ value });
    const action = document.createElement("div");
    action.id = "file-action";
    document.body.append(action);
    render(SecretValueButton(secret), action);
    action.querySelector("button")!.click();
    await vi.waitFor(() => expect(downloadFile).toHaveBeenCalledOnce());
    const download = vi.mocked(downloadFile).mock.calls[0][0];
    expect(download.filename).toBe(secret.name);
    expect(new Uint8Array(download.content as ArrayBuffer)).toEqual(bytes);
});
