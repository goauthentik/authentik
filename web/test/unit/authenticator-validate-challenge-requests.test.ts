import { singleFlight } from "#flow/stages/authenticator_validate/challenge-requests";

import { describe, expect, it, vi } from "vitest";

function deferred<T>() {
    let resolve!: (value: T) => void;
    let reject!: (reason: unknown) => void;

    const promise = new Promise<T>((accept, fail) => {
        resolve = accept;
        reject = fail;
    });

    return { promise, resolve, reject };
}

describe("singleFlight", () => {
    it("shares an in-flight selection request with an immediate resend", async () => {
        const response = deferred<string>();
        const send = vi.fn(() => response.promise);
        const request = singleFlight(send);
        const selection = request("email-1");
        const resend = request("email-1");

        expect(resend).toBe(selection);
        await Promise.resolve();
        expect(send).toHaveBeenCalledTimes(1);
        response.resolve("sent");
        await expect(resend).resolves.toBe("sent");
    });

    it("allows another send immediately after the previous request completes", async () => {
        const send = vi.fn().mockResolvedValue("sent");
        const request = singleFlight(send);
        await request("email-1");
        await request("email-1");

        expect(send).toHaveBeenCalledTimes(2);
    });

    it("allows retry after a failed request", async () => {
        const send = vi
            .fn()
            .mockRejectedValueOnce(new Error("unavailable"))
            .mockResolvedValue("sent");

        const request = singleFlight(send);
        await expect(request("email-1")).rejects.toThrow("unavailable");
        await expect(request("email-1")).resolves.toBe("sent");

        expect(send).toHaveBeenCalledTimes(2);
    });

    it("keeps requests for different devices independent", async () => {
        const first = deferred<string>();

        const send = vi.fn((device: string) =>
            device === "email-1" ? first.promise : Promise.resolve("sent"),
        );

        const request = singleFlight(send);
        const pending = request("email-1");
        await expect(request("email-2")).resolves.toBe("sent");
        first.resolve("sent");
        await pending;

        expect(send).toHaveBeenCalledTimes(2);
    });
});
