import type { FlowChallengeResponseRequestBody, SubmitOptions, SubmitRequest } from "#flow/types";

import { ChallengeTypes, ContextualFlowInfo } from "@goauthentik/api";

const PROPAGATES = { bubbles: true, composed: true };

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
        super(AKFlowInspectorChangeEvent.eventName, PROPAGATES);

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
}

/**
 * Event dispatched when the state of the interface drawers changes.
 */
export class AKFlowAdvanceEvent extends Event {
    public static readonly eventName = "ak-flow-advance";

    constructor() {
        super(AKFlowAdvanceEvent.eventName, PROPAGATES);
    }
}

//#endregion

//#region Executor control

/**
 * Event dispatched to request that the challenge be progressed from the client side.
 */
export class AKFlowUpdateChallengeRequest extends Event {
    public static readonly eventName = "ak-flow-update-challenge";
    public challenge: ChallengeTypes;

    constructor(challenge: ChallengeTypes) {
        super(AKFlowUpdateChallengeRequest.eventName, PROPAGATES);
        this.challenge = challenge;
    }
}

export class AKFlowSubmitRequest extends Event {
    public static readonly eventName = "ak-flow-submit-request";
    public readonly request: SubmitRequest;

    constructor(
        payload: FlowChallengeResponseRequestBody,
        options: SubmitOptions = { invisible: false },
    ) {
        super(AKFlowSubmitRequest.eventName, PROPAGATES);
        this.request = {
            payload,
            options,
        };
    }
}

export class AKFlowInfoUpdateEvent extends Event {
    public static readonly eventName = "ak-flow-info-update-event";
    public flowInfo: ContextualFlowInfo | null = null;

    constructor(flowInfo?: ContextualFlowInfo) {
        super(AKFlowInfoUpdateEvent.eventName, PROPAGATES);
        this.flowInfo = flowInfo ?? null;
    }
}

// This is subtle: we don't actually *care* about the Promise's payload; we only care to show some
// "loading" message (spinner, skeleton, whatever) when there's a network transaction underway. So
// when we start a transaction, we send a copy of its promise in an event; upon receipt, a listener
// can show whatever visual effect is desired, then listen for the promise to resolve, then stop the
// visual effect. Complete separation and independence.
//
export class AKFlowLoadingEvent extends Event {
    public static readonly eventName = "ak-flow-loading-event";
    public awaiter: Promise<unknown>;
    constructor(awaiter: Promise<unknown>) {
        super(AKFlowLoadingEvent.eventName, PROPAGATES);
        this.awaiter = awaiter;
    }
}

//#endregion

declare global {
    interface WindowEventMap {
        [AKFlowAdvanceEvent.eventName]: AKFlowAdvanceEvent;
        [AKFlowInspectorChangeEvent.eventName]: AKFlowInspectorChangeEvent;
    }

    interface HTMLElementEventMap {
        [AKFlowSubmitRequest.eventName]: AKFlowSubmitRequest;
        [AKFlowInfoUpdateEvent.eventName]: AKFlowInfoUpdateEvent;
        [AKFlowLoadingEvent.eventName]: AKFlowLoadingEvent;
        [AKFlowUpdateChallengeRequest.eventName]: AKFlowUpdateChallengeRequest;
    }
}
