import { FORM_FIELD_SETTLE_TIMEOUT, settleFormFields } from "#elements/forms/settle-form-fields";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

/**
 * `settleFormFields` only reads `form.elements`, so a plain object stands in for the form.
 */
function makeForm(...elements: object[]): HTMLFormElement {
    return { elements } as unknown as HTMLFormElement;
}

const pending = () => new Promise<void>(() => {});

describe("settleFormFields", () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it("resolves immediately when no field is settling", async () => {
        await expect(settleFormFields(makeForm({}, { value: "x" }))).resolves.toBeUndefined();
    });

    it("waits for every settling field", async () => {
        let release!: () => void;

        const settled = new Promise<void>((resolve) => {
            release = resolve;
        });

        const onSettled = vi.fn();

        settleFormFields(makeForm({ settled: Promise.resolve() }, { settled })).then(onSettled);

        await vi.advanceTimersByTimeAsync(0);
        expect(onSettled).not.toHaveBeenCalled();

        release();
        await vi.advanceTimersByTimeAsync(0);
        expect(onSettled).toHaveBeenCalledOnce();
    });

    it("resolves when a field's promise rejects", async () => {
        await expect(
            settleFormFields(makeForm({ settled: Promise.reject(new Error("network")) })),
        ).resolves.toBeUndefined();
    });

    it("gives up on a field that never settles after the timeout", async () => {
        const onSettled = vi.fn();
        settleFormFields(makeForm({ settled: pending() })).then(onSettled);

        await vi.advanceTimersByTimeAsync(FORM_FIELD_SETTLE_TIMEOUT - 1);
        expect(onSettled).not.toHaveBeenCalled();

        await vi.advanceTimersByTimeAsync(1);
        expect(onSettled).toHaveBeenCalledOnce();
    });

    it("honors a custom timeout", async () => {
        const onSettled = vi.fn();
        settleFormFields(makeForm({ settled: pending() }), 50).then(onSettled);

        await vi.advanceTimersByTimeAsync(50);
        expect(onSettled).toHaveBeenCalledOnce();
    });
});
