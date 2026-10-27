import { refreshServerContext } from "#common/global";

import { Broadcast } from "#flow/tabs/broadcast";
import { BroadcastMessage, BroadcastMessageType } from "#flow/tabs/messages";
import { multiTabOrchestrateResume } from "#flow/tabs/orchestrator";

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const lockName = "ak:tab_locked";

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

    document.getElementById("ak-brand")?.remove();
    refreshServerContext();
});

describe("multiTabOrchestrateResume", () => {
    it("bows out while another tab holds the lock", async () => {
        const broadcast = new RespondingBroadcast(new Set(["leader", "follower"]));
        const resumeTab = vi.spyOn(broadcast, "resumeTab");
        const suppressNextExit = vi.spyOn(broadcast, "suppressNextExit");

        await navigator.locks.request(lockName, () =>
            withSharedBroadcast(broadcast, () => multiTabOrchestrateResume()),
        );

        expect(resumeTab).not.toHaveBeenCalled();
        expect(suppressNextExit).toHaveBeenCalledOnce();
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

            // The lock is granted asynchronously, so keep advancing until the leader is done.
            await vi.waitFor(async () => {
                await vi.advanceTimersByTimeAsync(EVENTUALLY_MS);

                expect(settled).toBe(true);
            });

            await orchestration;
        });

        expect(resumeTab).toHaveBeenCalledOnce();
    });
});
