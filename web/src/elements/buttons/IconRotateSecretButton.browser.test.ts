import { IconRotateSecretButton } from "#elements/buttons/IconRotateSecretButton";
import { showMessage } from "#elements/messages/MessageContainer";
import { RouteChangeEvent } from "#elements/router/events";

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

test.each([false, true])("rotation completes once even after navigation: %s", async (navigate) => {
    vi.mocked(showMessage).mockClear();
    const response = Promise.withResolvers<{ value: string | null }>();
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
    if (navigate) {
        window.dispatchEvent(new Event(RouteChangeEvent.eventName));
        await vi.waitFor(() => expect(dialog.isConnected).toBe(false));
    }
    response.resolve({ value: navigate ? "replacement" : null });
    await vi.waitFor(() => expect(dialog.isConnected).toBe(false));
    if (navigate) {
        await vi.waitFor(() =>
            expect(document.querySelector("ak-hidden-text-input")?.getAttribute("value")).toBe(
                "replacement",
            ),
        );
        document.querySelector<HTMLDialogElement>("dialog[open]")!.close();
    }
    await vi.waitFor(() => expect(showMessage).toHaveBeenCalledTimes(1));
});
