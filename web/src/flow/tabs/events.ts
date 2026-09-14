export class AKMultiTabEvent extends Event {
    static readonly eventName = "ak-multitab-continue";

    constructor() {
        super(AKMultiTabEvent.eventName, { bubbles: true, composed: true });
    }
}

export class AKMultiTabExitEvent extends Event {
    static readonly eventName = "ak-multitab-exit";

    public readonly tabID: string;
    public readonly resumeID: string | null;

    constructor(tabID: string, resumeID: string | null = null) {
        super(AKMultiTabExitEvent.eventName, { bubbles: true, composed: true });

        this.tabID = tabID;
        this.resumeID = resumeID;
    }
}

declare global {
    interface WindowEventMap {
        [AKMultiTabEvent.eventName]: AKMultiTabEvent;
        [AKMultiTabExitEvent.eventName]: AKMultiTabExitEvent;
    }
}
