/**
 * @file Flow event utilities.
 */

//#region Flow Inspector

/**
 * Event dispatched when flow inspector state changes.
 */
export class AKFlowInspectorChangeEvent extends Event {
    public static readonly eventName = "ak-flow-inspector-change";

    public readonly open: boolean;

    constructor(open: boolean) {
        super(AKFlowInspectorChangeEvent.eventName, { bubbles: true, composed: true });

        this.open = open;
    }

    //#region Static Dispatchers

    /**
     * Dispatches an event to close flow inspector.
     */
    public static dispatchClose() {
        window.dispatchEvent(new AKFlowInspectorChangeEvent(false));
    }

    /**
     * Dispatches an event to open flow inspector.
     */
    public static dispatchOpen() {
        window.dispatchEvent(new AKFlowInspectorChangeEvent(true));
    }

    //#endregion
}

declare global {
    interface WindowEventMap {
        [AKFlowInspectorChangeEvent.eventName]: AKFlowInspectorChangeEvent;
    }
}

//#endregion

//#region Flow Inspector

/**
 * Event dispatched when the state of the interface drawers changes.
 */
export class AKFlowAdvanceEvent extends Event {
    public static readonly eventName = "ak-flow-advance";

    constructor() {
        super(AKFlowAdvanceEvent.eventName, { bubbles: true, composed: true });
    }
}

declare global {
    interface WindowEventMap {
        [AKFlowAdvanceEvent.eventName]: AKFlowAdvanceEvent;
    }
}

//#endregion
