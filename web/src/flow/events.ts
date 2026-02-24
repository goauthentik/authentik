/**
 * @file Flow event utilities.
 */

import type { FlowChallengeResponseRequestBody, SubmitOptions, SubmitRequest } from "#flow/types";

import { ChallengeTypes } from "@goauthentik/api";

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

/**
 * Event dispatched when the state of the interface drawers changes.
 */
export class AKFlowAdvanceEvent extends Event {
    public static readonly eventName = "ak-flow-advance";

    constructor() {
        super(AKFlowAdvanceEvent.eventName, { bubbles: true, composed: true });
    }
}

/**
 *
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

declare global {
    interface WindowEventMap {
        [AKFlowInspectorChangeEvent.eventName]: AKFlowInspectorChangeEvent;
        [AKFlowAdvanceEvent.eventName]: AKFlowAdvanceEvent;
        [AKFlowUpdateChallengeRequest.eventName]: AKFlowUpdateChallengeRequest;
        [AKFlowSubmitRequest.eventName]: AKFlowSubmitRequest;
    }
}

//#endregion
