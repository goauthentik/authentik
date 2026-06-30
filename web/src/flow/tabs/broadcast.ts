import { AKMultiTabEvent, AKMultiTabExitEvent } from "#flow/tabs/events";
import { BroadcastMessage, BroadcastMessageType } from "#flow/tabs/messages";
import { TabID } from "#flow/tabs/TabID";

import { ConsoleLogger, Logger } from "#logger/browser";

import { match } from "ts-pattern";

export class Broadcast extends BroadcastChannel implements Disposable {
    public static readonly ChannelName = "authentik";
    public static readonly SessionStorageKey = "authentik_tab_resume_id";

    public static readonly shared = new Broadcast();

    protected discoveredTabIDs = new Set<string>();
    protected shouldSuppressExit = false;

    protected logger: Logger;
    protected storageKey: string;

    //#region Lifecycle

    constructor(
        channelName: string = Broadcast.ChannelName,
        storageKey: string = Broadcast.SessionStorageKey,
    ) {
        super(channelName);

        this.storageKey = storageKey;

        this.addEventListener("message", this.messageListener);
        window.addEventListener("pagehide", this.pageHideListener);

        this.logger = ConsoleLogger.prefix("mtab/broadcast");
    }

    public [Symbol.dispose]() {
        this.removeEventListener("message", this.messageListener);
        window.removeEventListener("pagehide", this.pageHideListener);
    }

    protected dispatchMessage(message: BroadcastMessage): void {
        this.logger.debug("dispatching message", message);

        this.postMessage(message);
    }

    //#endregion

    //#region Event Listeners

    protected messageListener = (event: MessageEvent<BroadcastMessage>): void => {
        this.logger.debug("broadcast event", event.data);

        match(event.data)
            .with({ type: BroadcastMessageType.Discover }, () => {
                if (event.data.sender === TabID.shared.current) {
                    return;
                }

                this.dispatchMessage({
                    type: BroadcastMessageType.DiscoverReply,
                    sender: TabID.shared.current,
                });
            })
            .with({ type: BroadcastMessageType.DiscoverReply }, ({ sender }) => {
                this.discoveredTabIDs.add(sender);
            })
            .with({ type: BroadcastMessageType.Exit }, ({ sender, resumeID }) => {
                window.dispatchEvent(new AKMultiTabExitEvent(sender, resumeID));
            })
            .with({ type: BroadcastMessageType.Continue }, ({ target, resumeID }) => {
                if (target !== TabID.shared.current) {
                    return;
                }

                if (typeof resumeID === "string") {
                    sessionStorage.setItem(this.storageKey, resumeID);
                }

                this.logger.debug("Continuing upon event");

                window.dispatchEvent(new AKMultiTabEvent());
            })
            .otherwise(() => {
                this.logger.warn("Unknown broadcast message type", event.data);
            });
    };

    protected pageHideListener = (): void => {
        if (this.shouldSuppressExit) {
            this.shouldSuppressExit = false;

            return;
        }

        return this.dispatchExit();
    };

    //#endregion

    //#region Public Methods

    /**
     * Sends a message to all other tabs to discover their tab IDs.
     *
     * @returns A promise that resolves with a set of discovered tab IDs.
     */
    public async discoverTabs(): Promise<Set<string>> {
        this.discoveredTabIDs.clear();

        this.dispatchMessage({
            type: BroadcastMessageType.Discover,
            sender: TabID.shared.current,
        });

        await new Promise<void>((r) => {
            setTimeout(r, 20);
        });

        return this.discoveredTabIDs;
    }

    /**
     * Sends a message to a specific tab to resume its operation.
     *
     * @param tabID The ID of the tab to resume.
     * @param resumeID The resume ID to send to the tab.
     */
    public resumeTab(tabID: string, resumeID: string): void {
        this.dispatchMessage({
            type: BroadcastMessageType.Continue,
            sender: TabID.shared.current,
            target: tabID,
            resumeID,
        });
    }

    /**
     * Sends a message to all other tabs to notify them that this tab is exiting.
     */
    public dispatchExit(): void {
        const resumeID = sessionStorage.getItem(this.storageKey);

        this.dispatchMessage({
            type: BroadcastMessageType.Exit,
            sender: TabID.shared.current,
            resumeID,
        });

        sessionStorage.removeItem(this.storageKey);
    }

    /**
     * Suppresses the next exit event that would be sent when the tab is closed or navigated away
     * from.
     *
     * This is useful for cases where the tab is being programmatically closed or navigated away
     * from, and we don't want to notify other tabs of the exit.
     *
     * This method should be called before the tab is closed or navigated away from, and it will
     * prevent the exit event from being sent to other tabs.
     */
    public suppressNextExit(): void {
        this.shouldSuppressExit = true;
    }

    //#endregion
}
