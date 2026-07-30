import type { Interface } from "#elements/Interface";

import { StageHost } from "#flow/types";

import { FlowChallengeResponseRequest } from "@goauthentik/api";

import { ReactiveController, ReactiveControllerHost } from "lit";

type MessageControllerHost = ReactiveControllerHost & Interface & StageHost;

interface MessageEvent {
    data: {
        message: string;
        source?: string;
        context?: string;
    };
}

/**
 * Coordinate with authentication events across iframe boundaries
 *
 * @remarks
 *
 * Third-party assistants in the authentication process, notably Device Compliance checks, are
 * loaded in iframes. This controller listens for iframe boundary-crossing events and, if
 * appropriate, forwards them to the FlowExecutor.
 *
 */
export class FlowIframeMessageController implements ReactiveController {
    #abortController: AbortController | null = null;

    constructor(private host: MessageControllerHost) {
        /* no op */
    }

    onMessage = (event: MessageEvent) => {
        const { source, context, message } = event.data;
        if (source === "goauthentik.io" && context === "flow-executor" && message === "submit") {
            this.host.submit({} as FlowChallengeResponseRequest, {
                invisible: true,
            });
        }
    };

    hostConnected() {
        this.#abortController?.abort();
        this.#abortController = new AbortController();
        const { signal } = this.#abortController;
        window.addEventListener("message", this.onMessage, { signal });
    }

    hostDisconnected() {
        this.#abortController?.abort();
        this.#abortController = null;
    }
}
