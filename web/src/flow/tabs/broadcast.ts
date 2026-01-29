import { TabID } from "#flow/tabs/TabID";

import { ConsoleLogger, Logger } from "#logger/browser";

export const BROADCAST_CHANNEL_NAME = "authentik";

enum BroadcastMessageType {
    discover = "discover",
    continue = "continue",
    exit = "exit",
    discoverReply = "discoverReply",
}

export interface BroadcastMessage {
    type: BroadcastMessageType;
    sender: string;
    [key: string]: unknown;
}

export class Broadcast extends BroadcastChannel {
    static shared = new Broadcast();

    private discoveredTabIds = new Set<string>();
    exitedTabIds: string[] = [];

    #logger: Logger;

    #onMessage = (ev: MessageEvent<BroadcastMessage>) => {
        this.#logger.debug("broadcast event", ev.data);
        switch (ev.data.type) {
            case BroadcastMessageType.discover:
                if (ev.data.sender === TabID.shared.current) {
                    return;
                }
                this.postMessage({
                    type: BroadcastMessageType.discoverReply,
                    sender: TabID.shared.current,
                });
                return;
            case BroadcastMessageType.discoverReply:
                this.discoveredTabIds.add(ev.data.sender as string);
                return;
            case BroadcastMessageType.exit:
                this.exitedTabIds.push(ev.data.sender);
                return;
            case BroadcastMessageType.continue:
                if (ev.data.target === TabID.shared.current) {
                    this.#logger.debug("Continuing upon event");
                    window.dispatchEvent(new CustomEvent("ak-multitab-continue"));
                }
                return;
        }
    };

    constructor() {
        super(BROADCAST_CHANNEL_NAME);
        this.addEventListener("message", this.#onMessage);
        this.#logger = ConsoleLogger.prefix("mtab/broadcast");
    }

    [Symbol.dispose]() {
        this.removeEventListener("message", this.#onMessage);
    }

    async akTabDiscover(): Promise<Set<string>> {
        this.discoveredTabIds.clear();
        this.postMessage({
            type: BroadcastMessageType.discover,
            sender: TabID.shared.current,
        });
        await new Promise<void>((r) => {
            setTimeout(r, 20);
        });
        return this.discoveredTabIds;
    }

    akResumeTab(tabId: string) {
        this.postMessage({
            type: BroadcastMessageType.continue,
            sender: TabID.shared.current,
            target: tabId,
        });
    }

    akExitTab() {
        this.postMessage({
            type: BroadcastMessageType.exit,
            sender: TabID.shared.current,
        });
    }
}
