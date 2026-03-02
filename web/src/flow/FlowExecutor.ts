import "#elements/LoadingOverlay";
import "#elements/locale/ak-locale-select";
import "#flow/components/ak-brand-footer";
import "#flow/components/ak-flow-card";
import "#flow/inspector/FlowInspectorButton";

import Styles from "./FlowExecutor.css" with { type: "bundled-text" };

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { globalAK } from "#common/global";
import { configureSentry } from "#common/sentry/index";
import { applyBackgroundImageProperty } from "#common/theme";
import { AKSessionAuthenticatedEvent } from "#common/ws/events";
import { WebsocketClient } from "#common/ws/WebSocketClient";

import { listen } from "#elements/decorators/listen";
import { Interface } from "#elements/Interface";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { WithBrandConfig } from "#elements/mixins/branding";
import { LitPropertyRecord, SlottedTemplateResult } from "#elements/types";
import { exportParts } from "#elements/utils/attributes";
import { ThemedImage } from "#elements/utils/images";

import {
    AKFlowAdvanceEvent,
    AKFlowSubmitRequest,
    AKFlowUpdateChallengeRequest,
} from "#flow/events";
import { StageMapping } from "#flow/FlowExecutorStageFactory";
import { BaseStage } from "#flow/stages/base";
import type {
    ExecutorMessage,
    FlowChallengeResponseRequestBody,
    StageHost,
    SubmitOptions,
} from "#flow/types";

import { ConsoleLogger } from "#logger/browser";

import {
    ChallengeTypes,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowLayoutEnum,
    FlowsApi,
} from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";
import { html as staticHTML, unsafeStatic } from "lit/static-html.js";

import PFBackgroundImage from "@patternfly/patternfly/components/BackgroundImage/background-image.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

/// <reference types="../../types/lit.d.ts" />

/**
 * An executor for authentik flows.
 *
 * @attr {string} slug - The slug of the flow to execute.
 * @prop {ChallengeTypes | null} challenge - The current challenge to render.
 *
 * @part main - The main container for the flow content.
 * @part content - The container for the stage content.
 * @part content-iframe - The iframe element when using a frame background layout.
 * @part footer - The footer container.
 * @part locale-select - The locale select component.
 * @part branding - The branding element, used for the background image in some layouts.
 * @part loading-overlay - The loading overlay element.
 * @part challenge-additional-actions - Container in stages which have additional actions.
 * @part challenge-footer-band - Container for the stage footer, used for additional actions in some stages.
 * @part locale-select-label - The label of the locale select component.
 * @part locale-select-select - The select element of the locale select component.
 */
@customElement("ak-flow-executor")
export class FlowExecutor extends WithBrandConfig(Interface) implements StageHost {
    public static readonly DefaultLayout: FlowLayoutEnum =
        globalAK()?.flow?.layout || FlowLayoutEnum.Stacked;

    //#region Styles

    static styles: CSSResult[] = [
        PFLogin,
        PFDrawer,
        PFButton,
        PFTitle,
        PFList,
        PFBackgroundImage,
        Styles,
    ];

    //#endregion

    //#region Properties

    @property({ type: String, attribute: "slug", useDefault: true })
    public flowSlug: string = window.location.pathname.split("/")[3];

    @property({ attribute: false })
    public challenge: ChallengeTypes | null = null;

    @property({ type: Boolean })
    public loading = false;

    @property({ type: String, attribute: "data-layout", useDefault: true, reflect: true })
    public layout: FlowLayoutEnum = FlowExecutor.DefaultLayout;

    //#endregion

    //#region Internal State

    #logger = ConsoleLogger.prefix("flow-executor");

    #api: FlowsApi;

    //#endregion

    //#region Accessors

    public get flowInfo() {
        return this.challenge?.flowInfo ?? null;
    }

    //region Live event handlers

    handleExecutorMessage = (event: MessageEvent<ExecutorMessage>) => {
        const { source, context, message } = event.data;

        if (source !== "goauthentik.io" && context !== "flow-executor" && message === "submit") {
            this.submit({} as FlowChallengeResponseRequest);
        }
    };

    handleChallengeRequest = (event: AKFlowUpdateChallengeRequest) => {
        this.challenge = event.challenge;
    };

    handleSubordinateSubmit = (event: AKFlowSubmitRequest) => {
        // prettier-ignore
        const { request: { payload, options } } = event;
        this.submit(payload, options);
    };

    //endregion

    //#region Lifecycle

    constructor() {
        configureSentry();

        super();

        WebsocketClient.connect();

        this.#api = new FlowsApi(DEFAULT_CONFIG);

        window.addEventListener("message", this.handleExecutorMessage);
        this.addEventListener(AKFlowUpdateChallengeRequest.eventName, this.handleChallengeRequest);
        this.addEventListener(AKFlowSubmitRequest.eventName, this.handleSubordinateSubmit);
    }

    /**
     * Synchronize flow info such as background image with the current state.
     */
    #synchronizeFlowInfo() {
        if (!this.flowInfo) return;

        if (this.layout === FlowLayoutEnum.SidebarLeftFrameBackground) return;
        if (this.layout === FlowLayoutEnum.SidebarRightFrameBackground) return;

        const background =
            this.flowInfo.backgroundThemedUrls?.[this.activeTheme] || this.flowInfo.background;

        // Storybook has a different document structure, so we need to adjust the target accordingly.
        const target =
            import.meta.env.AK_BUNDLER === "storybook"
                ? this.closest<HTMLDivElement>(".docs-story")
                : this.ownerDocument.body;

        applyBackgroundImageProperty(background, { target });
    }

    //#region Listeners

    @listen(AKSessionAuthenticatedEvent)
    protected sessionAuthenticatedListener = () => {
        if (!document.hidden) {
            return;
        }

        console.debug("authentik/ws: Reloading after session authenticated event");
        window.location.reload();
    };

    public disconnectedCallback(): void {
        super.disconnectedCallback();

        WebsocketClient.close();
    }

    private setFlowErrorChallenge(error: APIError) {
        this.challenge = {
            component: "ak-stage-flow-error",
            error: pluckErrorDetail(error),
            requestId: "",
        } satisfies FlowErrorChallenge as ChallengeTypes;
    }

    protected refresh = async () => {
        if (!this.flowSlug) {
            this.#logger.debug("Skipping refresh, no flow slug provided");
            return Promise.resolve();
        }

        this.loading = true;

        return this.#api
            .flowsExecutorGet({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
            })
            .then((challenge) => {
                this.challenge = challenge;
                return !!this.challenge;
            })
            .catch(async (error) => {
                const parsedError = await parseAPIResponseError(error);
                showAPIErrorMessage(parsedError);
                this.setFlowErrorChallenge(parsedError);
                return false;
            })
            .finally(() => {
                this.loading = false;
            });
    };

    public async firstUpdated(changed: PropertyValues<this>): Promise<void> {
        super.firstUpdated(changed);

        this.refresh().then(() => {
            window.dispatchEvent(new AKFlowAdvanceEvent());
        });
    }

    // DOM post-processing has to happen after the render.
    public updated(changedProperties: PropertyValues<this>) {
        super.updated(changedProperties);

        document.title = match(this.challenge?.flowInfo?.title)
            .with(P.nullish, () => this.brandingTitle)
            .otherwise((title) => `${title} - ${this.brandingTitle}`);

        if (changedProperties.has("challenge") && this.challenge?.flowInfo) {
            this.layout = this.challenge?.flowInfo?.layout || FlowExecutor.DefaultLayout;
        }

        if (changedProperties.has("flowInfo") || changedProperties.has("activeTheme")) {
            this.#synchronizeFlowInfo();
        }
    }

    //#endregion

    //#region Public Methods

    public submit = async (
        payload?: FlowChallengeResponseRequestBody,
        options?: SubmitOptions,
    ): Promise<boolean> => {
        if (!payload) throw new Error("No payload provided");
        if (!this.challenge) throw new Error("No challenge provided");

        if (!this.flowSlug) {
            if (import.meta.env.AK_BUNDLER === "storybook") {
                this.#logger.debug("Skipping submit flow slug check in storybook");

                return true;
            }

            throw new Error("No flow slug provided");
        }

        // This order is deliberate; the executor always specifies the component token.
        const flowChallengeResponseRequest = {
            ...payload,
            component: this.challenge.component as FlowChallengeResponseRequest["component"],
        } as FlowChallengeResponseRequest;

        if (!options?.invisible) {
            this.loading = true;
        }

        return this.#api
            .flowsExecutorSolve({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
                flowChallengeResponseRequest,
            })
            .then((challenge) => {
                window.dispatchEvent(new AKFlowAdvanceEvent());
                this.challenge = challenge;
                return !this.challenge.responseErrors;
            })
            .catch((error: APIError) => {
                this.setFlowErrorChallenge(error);
                return false;
            })
            .finally(() => {
                this.loading = false;
            });
    };

    //#region Render Challenge

    protected async renderChallenge(challenge: ChallengeTypes) {
        const stageEntry = StageMapping.registry.get(challenge.component);

        // The special cases!
        if (!stageEntry) {
            if (challenge.component === "xak-flow-shell") {
                return html`${unsafeHTML(challenge.body)}`;
            }

            return this.renderChallengeError(
                `No stage found for component: ${challenge.component}`,
            );
        }

        const challengeProps: LitPropertyRecord<BaseStage<NonNullable<typeof challenge>, object>> =
            {
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

        return staticHTML`<${unsafeStatic(tag)} ${props}></${unsafeStatic(tag)}>`;
    }

    protected renderChallengeError(error: unknown): SlottedTemplateResult {
        const detail = pluckErrorDetail(error);

        // eslint-disable-next-line no-console
        console.trace(error);

        const errorChallenge: FlowErrorChallenge = {
            component: "ak-stage-flow-error",
            error: detail,
            requestId: "",
        };

        return html`<ak-stage-flow-error .challenge=${errorChallenge}></ak-stage-flow-error>`;
    }

    //#endregion

    //#region Render

    protected renderLoading(): SlottedTemplateResult {
        return html`<slot name="placeholder"></slot>`;
    }

    protected renderFrameBackground(): SlottedTemplateResult {
        return guard([this.layout, this.challenge], () => {
            if (
                this.layout !== FlowLayoutEnum.SidebarLeftFrameBackground &&
                this.layout !== FlowLayoutEnum.SidebarRightFrameBackground
            ) {
                return nothing;
            }

            const src = this.challenge?.flowInfo?.background;

            if (!src) return nothing;

            return html`
                <div class="ak-c-login__content" part="content">
                    <iframe
                        class="ak-c-login__content-iframe"
                        part="content-iframe"
                        name="flow-content-frame"
                        src=${src}
                    ></iframe>
                </div>
            `;
        });
    }

    protected renderFooter(): SlottedTemplateResult {
        return guard([this.layout], () => {
            return html`<footer
                aria-label=${msg("Site footer")}
                name="site-footer"
                part="footer"
                class="pf-c-login__footer ${this.layout === FlowLayoutEnum.Stacked
                    ? "pf-m-dark"
                    : ""}"
            >
                <slot name="footer"></slot>
            </footer>`;
        });
    }

    protected override render(): SlottedTemplateResult {
        const { challenge, loading } = this;

        return html`<ak-locale-select
                part="locale-select"
                exportparts="label:locale-select-label,select:locale-select-select"
                class="pf-m-dark"
            ></ak-locale-select>

            <header class="pf-c-login__header">
                <ak-flow-inspector-button></ak-flow-inspector-button>
            </header>
            <main
                data-layout=${this.layout}
                class="pf-c-login__main"
                aria-label=${msg("Authentication form")}
                part="main"
            >
                <div class="pf-c-login__main-header pf-c-brand" part="branding">
                    ${ThemedImage({
                        src: this.brandingLogo,
                        alt: msg("authentik Logo"),
                        className: "branding-logo",
                        theme: this.activeTheme,
                        themedUrls: this.brandingLogoThemedUrls,
                    })}
                </div>
                ${loading && challenge ? html`<ak-loading-overlay></ak-loading-overlay>` : nothing}
                ${guard([challenge], () => {
                    return challenge?.component
                        ? until(this.renderChallenge(challenge))
                        : this.renderLoading();
                })}
            </main>
            ${this.renderFooter()}`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-executor": FlowExecutor;
    }
}
