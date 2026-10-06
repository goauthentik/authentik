import { afterEach, beforeEach, expect, it, vi } from "vitest";

interface MessageState {
    lifetime: number | undefined;
    onDismiss: (() => void) | undefined;
    timeoutID: ReturnType<typeof setTimeout> | number;
}
 
function scheduleDismiss(state: MessageState): void {
    clearTimeout(state.timeoutID as ReturnType<typeof setTimeout>);
    state.timeoutID = -1;
    if (typeof state.lifetime !== "number" || !isFinite(state.lifetime)) return;
    if (!state.onDismiss) return;
    state.timeoutID = setTimeout(state.onDismiss, state.lifetime);
}

function willUpdateOld(state: MessageState, changed: Map<string, unknown>): void {
    if (changed.has("lifetime") && state.lifetime) {
        scheduleDismiss(state);
    }
}

function willUpdateFixed(state: MessageState, changed: Map<string, unknown>): void {
    if ((changed.has("lifetime") && state.lifetime) || changed.has("onDismiss")) {
        scheduleDismiss(state);
    }
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());


it("OLD code: toast never auto-closes", () => {
    const state: MessageState = { lifetime: 5000, onDismiss: vi.fn(), timeoutID: -1 };
    willUpdateOld(state, new Map([["onDismiss", undefined]]));
    vi.advanceTimersByTime(10000);
    expect(state.onDismiss).not.toHaveBeenCalled(); // bug: timer never started
});

it("FIXED code: toast auto-closes after lifetime", () => {
    const state: MessageState = { lifetime: 5000, onDismiss: vi.fn(), timeoutID: -1 };
    willUpdateFixed(state, new Map([["onDismiss", undefined]]));
    vi.advanceTimersByTime(5000);
    expect(state.onDismiss).toHaveBeenCalledOnce(); // fix: timer starts
});

 