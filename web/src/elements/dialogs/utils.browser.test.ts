import { renderModal } from "#elements/dialogs";

import { expect, test, vi } from "vitest";

test("aborting a dialog disposes it once and preserves the count of other dialogs", async () => {
    const abort = new AbortController();
    const onDispose = vi.fn();
    const first = renderModal("First", { signal: abort.signal, onDispose });
    const second = renderModal("Second");
    await vi.waitFor(() => expect(document.querySelectorAll("dialog[open]")).toHaveLength(2));

    abort.abort();
    await first;
    await new Promise(requestAnimationFrame);
    await new Promise(requestAnimationFrame);
    const calls = onDispose.mock.calls.length;
    const count = document.documentElement.dataset.dialogCount;
    document.querySelector("dialog")!.close();
    await second;
    expect(calls).toBe(1);
    expect(count).toBe("1");
});
