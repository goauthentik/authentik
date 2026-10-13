import { showMessage } from "#elements/messages/MessageContainer";
import { RouterNavigateEvent } from "#elements/router/core/navigation";

import { RotateSecretButton } from "#admin/secrets/RotateSecretButton";

import { RotatedSecret, Secret, SecretsApi, SecretTypeEnum, UsedBy } from "@goauthentik/api";

import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { userEvent } from "vitest/browser";

import { render } from "lit";

vi.mock("#elements/messages/MessageContainer", async (importOriginal) => ({
    ...(await importOriginal<object>()),
    showMessage: vi.fn(),
}));

const container = document.createElement("div");
const secret: Secret = { pk: "secret-id", name: "test", type: SecretTypeEnum.Text } as Secret;

function mockUsedBy(usedBy: Partial<UsedBy>[] = []) {
    vi.spyOn(SecretsApi.prototype, "secretsSecretsUsedByList").mockResolvedValue(
        usedBy as UsedBy[],
    );
}

beforeEach(() => vi.stubEnv("AK_DOCS_URL", "https://docs.goauthentik.io"));

afterEach(async () => {
    document.querySelectorAll("dialog").forEach((dialog) => dialog.close());
    await vi.waitFor(() => expect(document.querySelector("dialog")).toBeNull());
    container.remove();
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
});

test.each([false, true])("rotation completes once even after navigation: %s", async (navigate) => {
    vi.mocked(showMessage).mockClear();
    mockUsedBy();
    const response = Promise.withResolvers<RotatedSecret>();

    const rotate = vi
        .spyOn(SecretsApi.prototype, "secretsSecretsRotateCreate")
        .mockReturnValue(response.promise);

    document.body.append(container);
    render(RotateSecretButton(secret), container);
    container.querySelector("button")!.click();
    await vi.waitFor(() => expect(document.querySelector("dialog")?.open).toBe(true));
    const dialog = document.querySelector("dialog")!;
    const confirm = dialog.querySelector<HTMLButtonElement>(".pf-m-danger")!;
    confirm.click();
    confirm.click();
    await userEvent.keyboard("{Escape}");
    expect(dialog.open).toBe(true);
    expect(rotate).toHaveBeenCalledTimes(1);

    if (navigate) {
        window.dispatchEvent(new Event(RouterNavigateEvent.eventName));
        await vi.waitFor(() => expect(dialog.isConnected).toBe(false));
    }

    response.resolve({ value: navigate ? "replacement" : null });
    await vi.waitFor(() => expect(dialog.isConnected).toBe(false));

    if (navigate) {
        await vi.waitFor(() =>
            expect(document.querySelector("ak-secret-value")?.getAttribute("value")).toBe(
                "replacement",
            ),
        );

        document.querySelector<HTMLDialogElement>("dialog[open]")!.close();
    }

    await vi.waitFor(() => expect(showMessage).toHaveBeenCalledTimes(1));
});

test.each([
    ["proxyprovider", true],
    ["oauth2provider", false],
])("rotation warns about proxy sessions when used by a %s: %s", async (modelName, warns) => {
    mockUsedBy([{ modelName }]);
    document.body.append(container);
    render(RotateSecretButton(secret), container);
    container.querySelector("button")!.click();
    await vi.waitFor(() => expect(document.querySelector("dialog")?.open).toBe(true));

    expect(document.querySelector("dialog")?.textContent?.includes("signs out every user")).toBe(
        warns,
    );
});

test("rotation links documentation and masks the result in a styled field", async () => {
    mockUsedBy();

    const rotate = vi
        .spyOn(SecretsApi.prototype, "secretsSecretsRotateCreate")
        .mockResolvedValue({ value: "replacement" });

    document.body.append(container);
    render(RotateSecretButton(secret), container);
    container.querySelector("button")!.click();
    await vi.waitFor(() => expect(document.querySelector("dialog")?.open).toBe(true));

    expect(rotate).not.toHaveBeenCalled();

    expect(document.querySelector<HTMLAnchorElement>("dialog a")?.href).toContain(
        "/sys-mgmt/secrets/manage-secrets/#rotate-a-secret",
    );

    document.querySelector<HTMLButtonElement>("dialog .pf-m-danger")!.click();

    await vi.waitFor(() =>
        expect(
            document.querySelector("ak-secret-value")?.shadowRoot?.querySelector("input"),
        ).toBeTruthy(),
    );

    const display = document.querySelector("ak-secret-value")!;
    const input = display.shadowRoot!.querySelector("input")!;
    expect(input.type).toBe("password");
    expect(input.value).toBe("replacement");
    expect(input.readOnly).toBe(true);
    await vi.waitFor(() => expect(input.getBoundingClientRect().width).toBeGreaterThan(0));

    expect(input.getBoundingClientRect().width).toBeGreaterThan(
        display.getBoundingClientRect().width * 0.65,
    );
});
