import { ResendFeedback } from "#flow/stages/resend-feedback";

import { afterEach, describe, expect, it, vi } from "vitest";

const host = () => ({ addController: vi.fn(), requestUpdate: vi.fn() });

afterEach(() => vi.useRealTimers());

describe("email resend feedback", () => {
    it("disables during the request and shows success for fifteen seconds", async () => {
        vi.useFakeTimers();
        const feedback = new ResendFeedback(host());
        let resolve!: (sent: boolean) => void;

        const send = vi.fn(
            () =>
                new Promise<boolean>((done) => {
                    resolve = done;
                }),
        );

        const request = feedback.run(send);
        expect(feedback.state).toBe("sending");
        await feedback.run(send);
        expect(send).toHaveBeenCalledTimes(1);
        resolve(true);
        await request;
        expect(feedback.state).toBe("sent");
        await vi.advanceTimersByTimeAsync(14999);
        expect(feedback.state).toBe("sent");
        await vi.advanceTimersByTimeAsync(1);
        expect(feedback.state).toBe("idle");
        await feedback.run(async () => true);
        expect(feedback.state).toBe("sent");
    });

    it("does not show success for a rejected send or transport failure", async () => {
        const feedback = new ResendFeedback(host());
        await feedback.run(async () => false);
        expect(feedback.state).toBe("idle");

        await feedback.run(async () => {
            throw new Error("network");
        });

        expect(feedback.state).toBe("idle");
    });

    it("clears feedback on disconnect and ignores a late response", async () => {
        vi.useFakeTimers();
        const feedback = new ResendFeedback(host());
        let resolve!: (sent: boolean) => void;

        const request = feedback.run(
            () =>
                new Promise<boolean>((done) => {
                    resolve = done;
                }),
        );

        feedback.hostDisconnected();
        resolve(true);
        await request;
        expect(feedback.state).toBe("idle");
        await feedback.run(async () => true);
        expect(feedback.state).toBe("sent");
        feedback.hostDisconnected();
        expect(vi.getTimerCount()).toBe(0);
        expect(feedback.state).toBe("idle");
    });
});
