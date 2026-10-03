import { refreshServerContext } from "#common/global";

import { Broadcast } from "#flow/tabs/broadcast";
import { BroadcastMessage, BroadcastMessageType } from "#flow/tabs/messages";
import { multiTabOrchestrateResume } from "#flow/tabs/orchestrator";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const lockKey = "authentik-tab-locked";

// Longer than any follower wait, so these tests don't depend on the orchestrator's timeouts.
const EVENTUALLY_MS = 10 * 60_000;

/**
 * Inject the brand the server would render into the document, with continuous login enabled.
 */
function enableContinuousLogin(): void {
    const script = document.createElement("script");

    script.type = "application/json";
    script.id = "ak-brand";

    script.textContent = JSON.stringify({
        ui_footer_links: [],
        flags: { flows_continuous_login: true },
    });

    document.head.append(script);
    refreshServerContext();
}

/**
 * A broadcast that answers every discovery round with the given tab IDs, without a real channel.
 */
class RespondingBroadcast extends Broadcast {
    constructor(public replies: Set<string>) {
        super(`authentik-test-${crypto.randomUUID()}`);
    }

    protected override dispatchMessage(message: BroadcastMessage): void {
        if (message.type !== BroadcastMessageType.Discover) return;

        for (const tabID of this.replies) {
            this.discoveredTabIDs.add(tabID);
        }
    }
}

/**
 * Run `callback` with `broadcast` standing in for {@linkcode Broadcast.shared}.
 */
async function withSharedBroadcast(
    broadcast: Broadcast,
    callback: () => Promise<void>,
): Promise<void> {
    const shared = Broadcast.shared;

    Object.defineProperty(Broadcast, "shared", { configurable: true, value: broadcast });

    try {
        await callback();
    } finally {
        Object.defineProperty(Broadcast, "shared", { configurable: true, value: shared });

        broadcast[Symbol.dispose]();
        broadcast.close();
    }
}

beforeEach(() => {
    enableContinuousLogin();
});

afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();

    localStorage.removeItem(lockKey);
    document.getElementById("ak-brand")?.remove();
    refreshServerContext();
});

describe("multiTabOrchestrateResume", () => {
    it("takes and releases the tab lock when no other tabs are open", async () => {
        vi.spyOn(Broadcast.prototype, "discoverTabs").mockResolvedValue(new Set());

        const setItem = vi.spyOn(Storage.prototype, "setItem");

        await multiTabOrchestrateResume();

        expect(setItem).toHaveBeenCalledWith(lockKey, expect.any(String));
        expect(localStorage.getItem(lockKey)).toBeNull();
    });

    it("bows out when the tab holding the lock is still open", async () => {
        localStorage.setItem(lockKey, "leader");

        const broadcast = new RespondingBroadcast(new Set(["leader", "follower"]));
        const resumeTab = vi.spyOn(broadcast, "resumeTab");
        const suppressNextExit = vi.spyOn(broadcast, "suppressNextExit");

        await withSharedBroadcast(broadcast, () => multiTabOrchestrateResume());

        expect(resumeTab).not.toHaveBeenCalled();
        expect(suppressNextExit).toHaveBeenCalledOnce();
        expect(localStorage.getItem(lockKey)).toBe("leader");
    });

    it("releases the tab lock when resuming a tab throws", async () => {
        vi.useFakeTimers();

        const broadcast = new RespondingBroadcast(new Set(["follower"]));

        vi.spyOn(broadcast, "resumeTab").mockImplementation(() => {
            throw new Error("Broadcast failed");
        });

        await withSharedBroadcast(broadcast, async () => {
            const orchestration = expect(multiTabOrchestrateResume()).rejects.toThrow(
                "Broadcast failed",
            );

            await vi.advanceTimersByTimeAsync(EVENTUALLY_MS);
            await orchestration;
        });

        expect(localStorage.getItem(lockKey)).toBeNull();
    });

    it("resumes a follower that never exits only once", async () => {
        vi.useFakeTimers();

        // A follower that answers every discovery round but never sends its exit event.
        const broadcast = new RespondingBroadcast(new Set(["follower"]));
        const resumeTab = vi.spyOn(broadcast, "resumeTab").mockImplementation(() => {});

        await withSharedBroadcast(broadcast, async () => {
            let settled = false;

            const orchestration = multiTabOrchestrateResume().then(() => {
                settled = true;
            });

            await vi.advanceTimersByTimeAsync(EVENTUALLY_MS);

            expect(settled).toBe(true);

            await orchestration;
        });

        expect(resumeTab).toHaveBeenCalledOnce();
    });

    it("stops waiting for a follower when checking whether it is still open fails", async () => {
        vi.useFakeTimers();

        const broadcast = new RespondingBroadcast(new Set(["follower"]));
        const resumeTab = vi.spyOn(broadcast, "resumeTab").mockImplementation(() => {});

        await withSharedBroadcast(broadcast, async () => {
            let settled = false;

            const orchestration = multiTabOrchestrateResume().then(() => {
                settled = true;
            });

            // Let the initial discovery finish, then fail every later check.
            await vi.advanceTimersByTimeAsync(20);

            vi.spyOn(broadcast, "discoverTabs").mockRejectedValue(new Error("Broadcast failed"));

            await vi.advanceTimersByTimeAsync(EVENTUALLY_MS);

            expect(settled).toBe(true);

            await orchestration;
        });

        expect(resumeTab).toHaveBeenCalledOnce();
    });
});
