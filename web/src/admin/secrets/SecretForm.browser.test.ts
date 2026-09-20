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

afterEach(async () => {
    document.querySelectorAll("dialog").forEach((dialog) => dialog.close());
    await vi.waitFor(() => expect(document.querySelector("dialog")).toBeNull());

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
        expect(form.shadowRoot?.querySelector('input[type="file"]')).toBeTruthy(),
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

test.each([SecretTypeEnum.Text, SecretTypeEnum.Multiline])(
    "views %s secrets in a styled modal",
    async (type) => {
        const value = "a secret value\nwith another line";

        vi.spyOn(SecretsApi.prototype, "secretsSecretsViewValueRetrieve").mockResolvedValue({
            value,
        });

        const action = document.createElement("div");
        action.id = "file-action";
        document.body.append(action);
        render(SecretValueButton({ pk: "secret-id", name: "Secret", type }), action);
        action.querySelector("button")!.click();

        await vi.waitFor(() =>
            expect(document.querySelector("ak-secret-value")?.shadowRoot).toBeTruthy(),
        );

        const display = document.querySelector("ak-secret-value")!;
        await display.updateComplete;

        await vi.waitFor(() =>
            expect(display.shadowRoot!.querySelector("input, textarea")).toBeTruthy(),
        );

        const input = display.shadowRoot!.querySelector<HTMLInputElement | HTMLTextAreaElement>(
            "input, textarea",
        )!;

        expect(input.readOnly).toBe(true);
        await vi.waitFor(() => expect(input.getBoundingClientRect().width).toBeGreaterThan(0));

        expect(input.getBoundingClientRect().width).toBeGreaterThan(
            display.getBoundingClientRect().width * 0.65,
        );

        if (type === SecretTypeEnum.Text) {
            expect(input.type).toBe("password");
            display.shadowRoot!.querySelector("ak-visibility-toggle")!.click();
            await vi.waitFor(() => expect(input.type).toBe("text"));
        } else {
            expect(input.value).toBe(value);
            expect((input as HTMLTextAreaElement).rows).toBe(4);
        }

        document.querySelector("dialog")!.close();
    },
);

test.each([SecretTypeEnum.Text, SecretTypeEnum.Multiline])(
    "modifying an existing %s secret requires opting in",
    async (type) => {
        const secret: Secret = { pk: "secret-id", name: "Secret", type };
        vi.spyOn(SecretsApi.prototype, "secretsSecretsRetrieve").mockResolvedValue(secret);

        const update = vi
            .spyOn(SecretsApi.prototype, "secretsSecretsPartialUpdate")
            .mockResolvedValue(secret);

        const form = document.createElement("ak-secret-form");
        form.instancePk = secret.pk;
        document.body.append(form);

        await vi.waitFor(() =>
            expect(
                form.shadowRoot
                    ?.querySelector("ak-secret-text-input, ak-secret-textarea-input")
                    ?.querySelector("button"),
            ).toBeTruthy(),
        );

        const control = form.shadowRoot!.querySelector(
            "ak-secret-text-input, ak-secret-textarea-input",
        )!;

        expect(control.querySelector("input[disabled]")).toBeTruthy();
        await form.submit(new SubmitEvent("submit"));
        expect(update.mock.calls[0][0].patchedSecretRequest.value).toBeUndefined();

        await vi.waitFor(() =>
            expect(
                form.shadowRoot!.querySelector("ak-secret-text-input, ak-secret-textarea-input"),
            ).toBeTruthy(),
        );

        const refreshed = form.shadowRoot!.querySelector(
            "ak-secret-text-input, ak-secret-textarea-input",
        )!;

        refreshed.querySelector("button")!.click();
        await vi.waitFor(() => expect(refreshed.querySelector("input[disabled]")).toBeNull());
        expect(form.shadowRoot!.activeElement).toBe(refreshed.querySelector("input, textarea"));
    },
);

test("a restricted create form submits its allowed type", async () => {
    const secret: Secret = { pk: "secret-id", name: "Secret", type: SecretTypeEnum.Multiline };
    const create = vi.spyOn(SecretsApi.prototype, "secretsSecretsCreate").mockResolvedValue(secret);
    const form = document.createElement("ak-secret-form");
    form.types = [SecretTypeEnum.Multiline];
    document.body.append(form);
    await vi.waitFor(() => expect(form.shadowRoot?.querySelector("textarea")).toBeTruthy());
    expect(form.shadowRoot!.querySelector("ak-radio-input")).toBeNull();
    const name = form.shadowRoot!.querySelector("ak-text-input")!;
    name.value = "Secret";
    await name.updateComplete;
    const value = form.shadowRoot!.querySelector("textarea")!;
    value.value = "key: value";
    value.dispatchEvent(new InputEvent("input", { bubbles: true }));
    await form.submit(new SubmitEvent("submit"));
    expect(create.mock.calls[0][0].secretRequest.type).toBe(SecretTypeEnum.Multiline);
});

test("upload covers its button and forgets a file when changing type", async () => {
    const form = document.createElement("ak-secret-form");
    document.body.append(form);
    await vi.waitFor(() => expect(form.shadowRoot?.querySelector("ak-radio-input")).toBeTruthy());

    const chooseType = async (value: SecretTypeEnum) => {
        const radio = form.shadowRoot!.querySelector("ak-radio-input")!;
        radio.value = value;
        radio.dispatchEvent(new InputEvent("input", { bubbles: true }));
        await form.updateComplete;
    };

    await chooseType(SecretTypeEnum.File);
    const input = form.shadowRoot!.querySelector<HTMLInputElement>('input[type="file"]')!;
    const transfer = new DataTransfer();
    transfer.items.add(new File(["contents"], "review-secret.txt"));
    input.files = transfer.files;
    input.dispatchEvent(new Event("change"));
    await form.updateComplete;

    expect(form.shadowRoot!.querySelector(".secret-file-name")?.textContent).toBe(
        "review-secret.txt",
    );

    const button = form.shadowRoot!.querySelector(".secret-upload")!;
    expect(input.getBoundingClientRect().height).toBeCloseTo(button.clientHeight, 0);
    expect(input.getBoundingClientRect().width).toBeCloseTo(button.clientWidth, 0);
    await chooseType(SecretTypeEnum.Text);
    await chooseType(SecretTypeEnum.File);

    expect(form.shadowRoot!.querySelector(".secret-file-name")?.textContent).toBe(
        "No file selected",
    );

    expect(
        form.shadowRoot!.querySelector<HTMLInputElement>('input[type="file"]')!.files!.length,
    ).toBe(0);
});
