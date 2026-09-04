import { IconRotateSecretButton } from "#elements/buttons/IconRotateSecretButton";

import { afterEach, expect, test, vi } from "vitest";
import { userEvent } from "vitest/browser";

import { render } from "lit";

vi.mock("#elements/messages/MessageContainer", async (importOriginal) => ({
    ...(await importOriginal<object>()),
    showMessage: vi.fn(),
}));

const container = document.createElement("div");

afterEach(() => {
    document.querySelectorAll("dialog").forEach((dialog) => dialog.close());
    container.remove();
});

test("rotation runs once and cannot be dismissed with Escape while pending", async () => {
    const response = Promise.withResolvers<{ value: null }>();
    const rotate = vi.fn(() => response.promise);
    document.body.append(container);
    render(IconRotateSecretButton({ rotate }), container);
    container.querySelector("button")!.click();
    await vi.waitFor(() => expect(document.querySelector("dialog")?.open).toBe(true));
    const dialog = document.querySelector("dialog")!;
    const confirm = dialog.querySelector<HTMLButtonElement>(".pf-m-danger")!;
    confirm.click();
    confirm.click();
    await userEvent.keyboard("{Escape}");
    expect(dialog.open).toBe(true);
    expect(rotate).toHaveBeenCalledTimes(1);
    response.resolve({ value: null });
    await vi.waitFor(() => expect(dialog.isConnected).toBe(false));
});
