import "#flow/stages/FlowErrorStage";
import "#flow/tabs/broadcast";

import { FlowIframeMessageController } from "./controllers/FlowIframeMessageController";
import { FlowMultitabController } from "./controllers/FlowMultitabController";

import { aki } from "#common/api/client";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { configureSentry } from "#common/sentry/index";

import { listen } from "#elements/decorators/listen";
import { light } from "#elements/directives/light";
import { Interface } from "#elements/Interface";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";
import { exportParts } from "#elements/utils/attributes";

import {
    AKFlowAdvanceEvent,
    AKFlowInfoUpdateEvent,
    AKFlowLoadingEvent,
    AKFlowSubmitRequest,
    AKFlowUpdateChallengeRequest,
} from "#flow/events";
import { StageMapping } from "#flow/FlowExecutorStageFactory";
import { BaseStage } from "#flow/stages/base";
import type { FlowChallengeResponseRequestBody, StageHost, SubmitOptions } from "#flow/types";

import { ConsoleLogger } from "#logger/browser";

import {
    ChallengeTypes,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowsApi,
} from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { observed } from "@patternfly/pfe-core/decorators/observed.js";
import { match } from "ts-pattern";

import { LOCALE_STATUS_EVENT, LocaleStatusEventDetail } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";
import { html as staticHTML, unsafeStatic } from "lit/static-html.js";

/// <reference types="../../types/lit.d.ts" />

type ChallengeProps = LitPropertyRecord<BaseStage<NonNullable<ChallengeTypes>, object>>;

/**
 * An executor for authentik flows
 *
 * @remarks
 *
 * - Controls the API transactions and the topmost Challenge
 * - Controls the transition from one Challenge to the next
 * - Loads and displays the current Stage according to the current Challenge
 * - Wraps all errors in a format that any application shell can display
 * - Provides the Iframe controller for third-party verifiers
 * - Provides the Multitab controller to send/receive messages to other tabs
 *   open to the current domain
 *
 * A *Flow* is a series of steps the authentik server takes to perform one of
 * its core functions, such as authentication, enrollment, or account recovery.
 * A *stage* is one step; a *challenge* is a stage that requires user input to
 * complete: you username, your password, an action with an MFA.
 *
 * The purpose of the FlowExecutor is to receive a challenge, select the
 * client-side component (also called "stages") best suited to showing the
 * request to the user, send the input to the server and deal with the response.
 *
 * @listens FlowUpdateChallenge - When a stage requires a change of Challenge
 *
 * @listens FlowSubmitRequest - When a stage has an out-of-band payload to
 * deliver to the server.
 *
 * @event FlowInfoUpdateEvent - Sent to the shell. May contain decorative
 * updates
 *
 * @event FlowLoadingEvent - Sent to the shell when a load from the server is
 * initiated. Carries a promise that resolves when a loading event ends. Used to
 * control show/hide of loading indicators.
 *
 * @event FlowAdvanceEvent - Sent to the shell when a stage transitions. Used to
 * notify any debuggers (such as the FlowInspector) to update its state.
 *
 * @attr {string} slug - The slug of the flow to execute.
 *
 * @prop {ChallengeTypes | null} challenge - The current challenge to render.
 *
 * @part main - The main container for the flow content.
 *
 * @part content - The container for the stage content.
 *
 * @part content-iframe - The iframe element when using a frame background layout.
 *
 * @part footer - The footer container.
 *
 * @part locale-select - The locale select component.
 *
 * @part challenge-additional-actions - Container in stages which have additional actions.
 *
 * @part challenge-footer-band - Container for the stage footer, used for additional actions in some stages.
 *
 * @part locale-select-label - The label of the locale select component.
 *
 * @part locale-select-select - The select element of the locale select component.
 *
 */
@customElement("ak-flow-executor")
export class FlowExecutor extends Interface implements StageHost {
    //#region Properties

    @property({ type: String, attribute: "slug", useDefault: true })
    public flowSlug: string = window.location.pathname.split("/")[3];

    // A new challenge can contain data that clients may want to use to alter
    // the look of the executor's container. Provide notice of those changes.

    @observed("handleFlowUpdate")
    @property({ attribute: false })
    public challenge: ChallengeTypes | null = null;

    //#endregion

    //#region Window Listeners

    @listen(LOCALE_STATUS_EVENT, { target: window })
    protected localeStatusListener = (event: CustomEvent<LocaleStatusEventDetail>) => {
        if (event.detail.status === "ready") {
            this.refresh();
        }
    };

    //#endregion

    //#region Internal State

    protected readonly logger = ConsoleLogger.prefix("flow-executor");

    private readonly api: FlowsApi;

    // Listen for challenge-forwarding events from iframe-based third-party
    // verifiers (Device Compliance)
    readonly #flowIframeMessageController = new FlowIframeMessageController(this);

    // Listen for authentik state-change events from other tabs
    readonly #flowMultitabController = new FlowMultitabController(this);

    //#endregion

    //region Live event handlers

    protected handleChallengeRequest = (event: AKFlowUpdateChallengeRequest) => {
        this.challenge = event.challenge;
    };

    protected handleSubordinateSubmit = (event: AKFlowSubmitRequest) => {
        // prettier-ignore
        const { request: { payload, options } } = event;
        this.submit(payload, options);
    };

    protected handleFlowUpdate() {
        this.dispatchEvent(new AKFlowInfoUpdateEvent(this.challenge?.flowInfo));
    }

    //endregion

    //#region Lifecycle

    constructor() {
        configureSentry();
        super();
        this.api = aki(FlowsApi);

        this.addController(this.#flowIframeMessageController);
        this.addController(this.#flowMultitabController);
        this.addEventListener(AKFlowUpdateChallengeRequest.eventName, this.handleChallengeRequest);
        this.addEventListener(AKFlowSubmitRequest.eventName, this.handleSubordinateSubmit);
    }

    private static buildChallengeError(error: APIError) {
        return {
            component: "ak-stage-flow-error",
            error: pluckErrorDetail(error),
            requestId: "",
        } satisfies FlowErrorChallenge as ChallengeTypes;
    }

    private setFlowErrorChallenge(error: APIError) {
        this.challenge = FlowExecutor.buildChallengeError(error);
    }

    protected refresh = async () => {
        if (!this.flowSlug) {
            this.logger.debug("Skipping refresh, no flow slug provided");
            return Promise.resolve();
        }

        const fetch = this.api.flowsExecutorGet({
            flowSlug: this.flowSlug,
            query: window.location.search.substring(1),
        });

        this.dispatchEvent(new AKFlowLoadingEvent(fetch));

        return fetch
            .then((challenge) => {
                this.challenge = challenge;
                return !!this.challenge;
            })
            .catch(async (error) => {
                const parsedError = await parseAPIResponseError(error);
                showAPIErrorMessage(parsedError);
                this.setFlowErrorChallenge(parsedError);
                return false;
            });
    };

    //#endregion

    //#region Public Methods

    public submit = async (payload?: FlowChallengeResponseRequestBody, options?: SubmitOptions) => {
        if (!payload) throw new Error("No payload provided");
        if (!this.challenge) throw new Error("No challenge provided");

        if (!this.flowSlug) {
            if (import.meta.env.AK_BUNDLER === "storybook") {
                this.logger.debug("Skipping submit flow slug check in storybook");
                return true;
            }

            throw new Error("No flow slug provided");
        }

        // The `as` clauses are necessary because OpenAPI doesn't really do
        // enums, it does records and unions of records. Alternatives to using
        // `as` would require putting the type being submitted into the `submit`
        // method's definition, and then modifying every stage to tell the
        // executor what type is being submitted. That would be lots of code for
        // no win; it's not coherent to think a stage for a request type will
        // submit a different request type. (It's possible, but if that doesn't
        // show up in testing we're in a mess anyway.)
        //
        // This order is deliberate; the executor always specifies the component
        // token.
        const { component } = this.challenge as FlowChallengeResponseRequest;

        const flowChallengeResponseRequest = {
            ...payload,
            component,
        } as FlowChallengeResponseRequest;

        const solve = this.api.flowsExecutorSolve({
            flowSlug: this.flowSlug,
            query: window.location.search.substring(1),
            flowChallengeResponseRequest,
        });

        if (!options?.invisible) {
            this.dispatchEvent(new AKFlowLoadingEvent(solve));
        }

        return solve
            .then((challenge) => {
                window.dispatchEvent(new AKFlowAdvanceEvent());
                this.challenge = challenge;
                return !this.challenge.responseErrors;
            })
            .catch((error: APIError) => {
                this.setFlowErrorChallenge(error);
                return false;
            });
    };

    //#region Render Challenge

    protected async renderChallengeSpecialCases(challenge: ChallengeTypes) {
        if (challenge.component === "xak-flow-shell") {
            return html`${unsafeHTML(challenge.body)}`;
        }

        return this.renderChallengeError(`No stage found for component: ${challenge.component}`);
    }

    protected async renderChallenge(challenge: ChallengeTypes) {
        const stageEntry = StageMapping.registry.get(challenge.component);

        if (!stageEntry) {
            return this.renderChallengeSpecialCases(challenge);
        }

        const challengeProps: ChallengeProps = {
            ".challenge": challenge,
            ".host": this,
        };

        const litParts = {
            part: "challenge",
            exportparts: exportParts(["additional-actions", "footer-band"], "challenge"),
        };

        let mapping: StageMapping;

        try {
            mapping = await StageMapping.from(stageEntry);
        } catch (error: unknown) {
            return this.renderChallengeError(error);
        }

        const { tag, variant } = mapping;

        const props = spread(
            match(variant)
                .with("challenge", () => challengeProps)
                .with("standard", () => ({ ...challengeProps, ...litParts }))
                .exhaustive(),
        );
        return light(staticHTML`<${unsafeStatic(tag)} ${props}></${unsafeStatic(tag)}>`);
    }

    protected renderChallengeError(error: unknown): SlottedTemplateResult {
        // eslint-disable-next-line no-console
        console.trace(error);

        const errorChallenge = FlowExecutor.buildChallengeError(error as APIError);
        return html`<ak-stage-flow-error .challenge=${errorChallenge}></ak-stage-flow-error>`;
    }

    protected renderPlaceholder() {
        return html`<slot name="placeholder"></slot>`;
    }

    //#endregion

    //#region Render

    protected override render(): SlottedTemplateResult {
        const { challenge } = this;
        return guard([challenge], () =>
            challenge?.component
                ? until(this.renderChallenge(challenge), this.renderPlaceholder())
                : this.renderPlaceholder(),
        );
    }

    //#endregion

    public override firstUpdated(changed: PropertyValues<this>) {
        super.firstUpdated(changed);
        this.refresh().then(() => {
            window.dispatchEvent(new AKFlowAdvanceEvent());
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-executor": FlowExecutor;
    }
}
