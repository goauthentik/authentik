import { TabID } from "#flow/tabs/TabID";

import { ConsoleLogger, Logger } from "#logger/browser";

export const BROADCAST_CHANNEL_NAME = "authentik";
export const SESSION_STORAGE_RESUME_ID = "authentik_tab_resume_id";

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

export interface BroadcastExitEventDetail {
    tabID: string;
    resumeID?: string;
}

export class Broadcast extends BroadcastChannel implements Disposable {
    static shared = new Broadcast();

    protected discoveredTabIDs = new Set<string>();
    public exitedTabIDs = new Map<string, string | undefined>();
    protected suppressNextExit = false;

    protected logger: Logger;

    protected messageListener = (ev: MessageEvent<BroadcastMessage>) => {
        this.logger.debug("broadcast event", ev.data);
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
                this.discoveredTabIDs.add(ev.data.sender as string);
                return;
            case BroadcastMessageType.exit:
                this.exitedTabIDs.set(ev.data.sender, ev.data.resumeID as string | undefined);
                window.dispatchEvent(
                    new CustomEvent<BroadcastExitEventDetail>("ak-multitab-exit", {
                        detail: {
                            tabID: ev.data.sender,
                            resumeID: ev.data.resumeID as string | undefined,
                        },
                    }),
                );
                return;
            case BroadcastMessageType.continue:
                if (ev.data.target === TabID.shared.current) {
                    if (typeof ev.data.resumeID === "string") {
                        sessionStorage.setItem(SESSION_STORAGE_RESUME_ID, ev.data.resumeID);
                    }
                    this.logger.debug("Continuing upon event");
                    window.dispatchEvent(new CustomEvent("ak-multitab-continue"));
                }
                return;
        }
    };

    protected pageHideListener = () => {
        if (this.suppressNextExit) {
            this.suppressNextExit = false;
            return;
        }
        this.akExitTab();
    };

    constructor() {
        super(BROADCAST_CHANNEL_NAME);

        this.addEventListener("message", this.messageListener);
        window.addEventListener("pagehide", this.pageHideListener);

        this.logger = ConsoleLogger.prefix("mtab/broadcast");
    }

    [Symbol.dispose]() {
        this.removeEventListener("message", this.messageListener);
    }

    async akTabDiscover(): Promise<Set<string>> {
        this.discoveredTabIDs.clear();
        this.exitedTabIDs.clear();

        this.postMessage({
            type: BroadcastMessageType.discover,
            sender: TabID.shared.current,
        });

        await new Promise<void>((r) => {
            setTimeout(r, 20);
        });

        return this.discoveredTabIDs;
    }

    akResumeTab(tabId: string, resumeID: string) {
        this.postMessage({
            type: BroadcastMessageType.continue,
            sender: TabID.shared.current,
            target: tabId,
            resumeID,
        });
    }

    akExitTab() {
        const resumeID = sessionStorage.getItem(SESSION_STORAGE_RESUME_ID) || undefined;
        this.postMessage({
            type: BroadcastMessageType.exit,
            sender: TabID.shared.current,
            resumeID,
        });
        sessionStorage.removeItem(SESSION_STORAGE_RESUME_ID);
    }

    akSuppressNextExit() {
        this.suppressNextExit = true;
    }
}
