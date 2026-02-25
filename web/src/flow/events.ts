import type { FlowChallengeResponseRequestBody, SubmitOptions, SubmitRequest } from "#flow/types";

import { ChallengeTypes } from "@goauthentik/api";

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
}

/**
 * Event dispatched when the state of the interface drawers changes.
 */
export class AKFlowAdvanceEvent extends Event {
    public static readonly eventName = "ak-flow-advance";

    constructor() {
        super(AKFlowAdvanceEvent.eventName, { bubbles: true, composed: true });
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
        super(AKFlowUpdateChallengeRequest.eventName, { bubbles: true, composed: true });
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
        super(AKFlowSubmitRequest.eventName, { bubbles: true, composed: true });
        this.request = {
            payload,
            options,
        };
    }
}

//#endregion

declare global {
    interface WindowEventMap {
        [AKFlowAdvanceEvent.eventName]: AKFlowAdvanceEvent;
        [AKFlowInspectorChangeEvent.eventName]: AKFlowInspectorChangeEvent;
        [AKFlowUpdateChallengeRequest.eventName]: AKFlowUpdateChallengeRequest;
    }
}
