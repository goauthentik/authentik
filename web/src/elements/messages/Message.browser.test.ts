import "#elements/messages/Message";
import type { Message } from "#elements/messages/Message";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { html, render } from "lit";

describe("ak-message dismiss timer", () => {
    let container: HTMLDivElement;

    beforeEach(() => {
        vi.useFakeTimers();
        container = document.body.appendChild(document.createElement("div"));
    });

    afterEach(() => {
        container.remove();
        vi.useRealTimers();
    });

    async function mount(lifetime: number, onDismiss: () => void) {
        render(
            html`<ak-message lifetime=${lifetime} .onDismiss=${onDismiss}>Hi</ak-message>`,
            container,
        );

        const element = container.querySelector<Message>("ak-message")!;
        await element.updateComplete;

        return element;
    }

    it("dismisses after lifetime", async () => {
        const onDismiss = vi.fn();
        await mount(1000, onDismiss);

        vi.advanceTimersByTime(999);
        expect(onDismiss).not.toHaveBeenCalled();
        vi.advanceTimersByTime(1);
        expect(onDismiss).toHaveBeenCalledOnce();
    });

    it("counts a changed lifetime from first render, not from the change", async () => {
        const onDismiss = vi.fn();
        const element = await mount(1000, onDismiss);

        vi.advanceTimersByTime(600);
        element.lifetime = 1500;
        await element.updateComplete;

        vi.advanceTimersByTime(899);
        expect(onDismiss).not.toHaveBeenCalled();
        vi.advanceTimersByTime(1);
        expect(onDismiss).toHaveBeenCalledOnce();
    });

    it("does not restart the clock when onDismiss is replaced", async () => {
        const first = vi.fn();
        const second = vi.fn();
        const element = await mount(1000, first);

        vi.advanceTimersByTime(600);
        element.onDismiss = second;
        await element.updateComplete;

        vi.advanceTimersByTime(400);
        expect(first).not.toHaveBeenCalled();
        expect(second).toHaveBeenCalledOnce();
    });

    it("never dismisses with an infinite lifetime", async () => {
        const onDismiss = vi.fn();
        await mount(Infinity, onDismiss);

        vi.advanceTimersByTime(60_000);
        expect(onDismiss).not.toHaveBeenCalled();
    });

    it("resumes the original deadline when re-attached", async () => {
        const onDismiss = vi.fn();
        const element = await mount(1000, onDismiss);

        vi.advanceTimersByTime(300);
        element.remove();
        vi.advanceTimersByTime(300);
        expect(onDismiss).not.toHaveBeenCalled();

        container.append(element);
        vi.advanceTimersByTime(399);
        expect(onDismiss).not.toHaveBeenCalled();
        vi.advanceTimersByTime(1);
        expect(onDismiss).toHaveBeenCalledOnce();
    });
});
