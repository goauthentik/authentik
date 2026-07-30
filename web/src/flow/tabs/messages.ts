export enum BroadcastMessageType {
    Discover = "discover",
    Continue = "continue",
    Exit = "exit",
    DiscoverReply = "discoverReply",
}

export interface BroadcastMessageDiscover {
    type: BroadcastMessageType.Discover;
    /**
     * The tab ID of the sender. This is used to prevent responding to your own messages.
     */
    sender: string;
}

export interface BroadcastMessageDiscoverReply {
    type: BroadcastMessageType.DiscoverReply;
    /**
     * The tab ID of the sender. This is used to prevent responding to your own messages.
     */
    sender: string;
}

export interface BroadcastMessageExit {
    type: BroadcastMessageType.Exit;
    /**
     * The tab ID of the sender. This is used to prevent responding to your own messages.
     */
    sender: string;
    /**
     * The resume ID of the tab. This is used to continue the tab's operation.
     */
    resumeID: string | null;
}

export interface BroadcastMessageContinue {
    type: BroadcastMessageType.Continue;
    /**
     * The tab ID of the sender. This is used to prevent responding to your own messages.
     */
    sender: string;
    /**
     * The tab ID of the target tab. This is used to direct the message to a specific tab.
     */
    target: string;
    /**
     * The resume ID of the tab. This is used to continue the tab's operation.
     */
    resumeID: string | null;
}

export type BroadcastMessage =
    | BroadcastMessageDiscover
    | BroadcastMessageDiscoverReply
    | BroadcastMessageExit
    | BroadcastMessageContinue;
