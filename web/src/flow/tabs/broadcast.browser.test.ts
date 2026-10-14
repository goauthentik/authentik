import { Broadcast } from "#flow/tabs/broadcast";
import { BroadcastMessage, BroadcastMessageType } from "#flow/tabs/messages";

import { describe, expect, it } from "vitest";

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

describe("Broadcast.discoverTabs", () => {
    it("returns a snapshot that later discovery rounds don't change", async () => {
        const broadcast = new RespondingBroadcast(new Set(["follower"]));

        try {
            const first = await broadcast.discoverTabs();

            broadcast.replies.clear();

            const second = await broadcast.discoverTabs();

            expect([...first]).toEqual(["follower"]);
            expect(second.size).toBe(0);
        } finally {
            broadcast[Symbol.dispose]();
            broadcast.close();
        }
    });
});
