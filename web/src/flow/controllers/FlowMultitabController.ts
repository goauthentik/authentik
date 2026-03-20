import type { Interface } from "#elements/Interface";

import { multiTabOrchestrateLeave } from "#flow/tabs/orchestrator";

import { ChallengeTypes, IdentificationChallenge } from "@goauthentik/api";

import { ReactiveController, ReactiveControllerHost } from "lit";

type MultitabControllerHost = ReactiveControllerHost &
    Interface & { challenge: ChallengeTypes | null };

const isChallenge = (v: unknown): v is ChallengeTypes =>
    v !== null && typeof v === "object" && "component" in v;

const isIdentificationChallenge = (v: unknown): v is IdentificationChallenge =>
    isChallenge(v) && v.component === "ak-stage-identification";

/**
 * Coordinate with authentication events across multiple tabs
 *
 * @remarks
 *
 * The RedirectStage triggers a change in authentication state. If there is more than one tab open
 * to authentik, this controller receives that event and, after checking with the context to ensure
 * coherency, redirects all tabs to the URL that reflects that state.
 *
 */
export class FlowMultitabController implements ReactiveController {
    #abortController: AbortController | null = null;

    constructor(private host: MultitabControllerHost) {
        /* no op */
    }

    onMultitab = () => {
        const { challenge } = this.host;
        if (!challenge) {
            return;
        }

        if (
            isIdentificationChallenge(challenge) &&
            challenge.applicationPreLaunch &&
            challenge.applicationPreLaunch !== "blank://blank"
        ) {
            multiTabOrchestrateLeave();
            window.location.assign(challenge.applicationPreLaunch);
            return;
        }

        const qs = new URLSearchParams(window.location.search);
        const next = qs.get("next");
        if (next) {
            const url = new URL(next, window.location.origin);
            if (url.origin !== window.location.origin) {
                multiTabOrchestrateLeave();
            }
            window.location.assign(url);
        }
    };

    hostConnected() {
        this.#abortController?.abort();
        this.#abortController = new AbortController();
        const { signal } = this.#abortController;
        window.addEventListener("ak-multitab-continue", this.onMultitab, { signal });
    }

    hostDisconnected() {
        this.#abortController?.abort();
        this.#abortController = null;
    }
}
