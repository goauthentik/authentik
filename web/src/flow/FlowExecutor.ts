import "#flow/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import "#elements/LoadingOverlay";
import "#elements/locale/ak-locale-select";
import "#flow/components/ak-brand-footer";
import "#flow/components/ak-flow-card";

import Styles from "./FlowExecutor.css" with { type: "bundled-text" };
import { stages } from "./FlowExecutorSelections";

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
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { LitPropertyRecord } from "#elements/types";
import { exportParts } from "#elements/utils/attributes";
import { ThemedImage } from "#elements/utils/images";

import { AKFlowAdvanceEvent, AKFlowInspectorChangeEvent } from "#flow/events";
import { BaseStage, StageHost, SubmitOptions } from "#flow/stages/base";

import { ConsoleLogger } from "#logger/browser";

import {
    CapabilitiesEnum,
    ChallengeTypes,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowLayoutEnum,
    FlowsApi,
    ShellChallenge,
} from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { match, P } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
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
 */
@customElement("ak-flow-executor")
export class FlowExecutor
    extends WithCapabilitiesConfig(WithBrandConfig(Interface))
    implements StageHost
{
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

    @property({ type: Boolean })
    public inspectorOpen?: boolean;

    @property({ type: Boolean })
    public inspectorAvailable?: boolean;

    @property({ type: String, attribute: "data-layout", useDefault: true, reflect: true })
    public layout: FlowLayoutEnum = FlowExecutor.DefaultLayout;

    //#endregion

    //#region State

    #inspectorLoaded = false;

    #logger = ConsoleLogger.prefix("flow-executor");

    //#endregion

    //#region Accessors

    public get flowInfo() {
        return this.challenge?.flowInfo ?? null;
    }

    //#region Lifecycle

    constructor() {
        configureSentry();

        super();

        WebsocketClient.connect();

        const inspector = new URLSearchParams(window.location.search).get("inspector");

        if (inspector === "" || inspector === "open") {
            this.inspectorOpen = true;
            this.inspectorAvailable = true;
        } else if (inspector === "available") {
            this.inspectorAvailable = true;
        }

        window.addEventListener("message", (event) => {
            const msg: {
                source?: string;
                context?: string;
                message: string;
            } = event.data;

            if (msg.source !== "goauthentik.io" || msg.context !== "flow-executor") {
                return;
            }
            if (msg.message === "submit") {
                this.submit({} as FlowChallengeResponseRequest);
            }
        });
    }

    /**
     * Synchronize flow info such as background image with the current state.
     */
    #synchronizeFlowInfo() {
        if (!this.flowInfo) {
            return;
        }

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

        return new FlowsApi(DEFAULT_CONFIG)
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

        if (this.can(CapabilitiesEnum.CanDebug)) {
            this.inspectorAvailable = true;
        }

        this.refresh().then(() => {
            if (this.inspectorOpen) {
                window.dispatchEvent(new AKFlowAdvanceEvent());
            }
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

        if (
            (changedProperties.has("flowInfo") || changedProperties.has("activeTheme")) &&
            this.flowInfo
        ) {
            this.#synchronizeFlowInfo();
        }

        if (
            changedProperties.has("inspectorOpen") &&
            this.inspectorOpen &&
            !this.#inspectorLoaded
        ) {
            import("#flow/FlowInspector").then(() => {
                this.#inspectorLoaded = true;
            });
        }
    }

    //#endregion

    //#region Public Methods

    public submit = async (
        payload?: FlowChallengeResponseRequest,
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

        payload.component = this.challenge.component as FlowChallengeResponseRequest["component"];

        if (!options?.invisible) {
            this.loading = true;
        }

        return new FlowsApi(DEFAULT_CONFIG)
            .flowsExecutorSolve({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
                flowChallengeResponseRequest: payload,
            })
            .then((challenge) => {
                if (this.inspectorOpen) {
                    window.dispatchEvent(new AKFlowAdvanceEvent());
                }

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

    protected async renderChallenge(
        component: ChallengeTypes["component"],
    ): Promise<TemplateResult> {
        const { challenge, inspectorOpen } = this;

        const stage = stages.get(component);

        // The special cases!
        if (!stage) {
            if (component === "xak-flow-shell") {
                return html`${unsafeHTML((challenge as ShellChallenge).body)}`;
            }
            return html`Invalid native challenge element`;
        }

        const challengeProps: LitPropertyRecord<BaseStage<NonNullable<typeof challenge>, unknown>> =
            { ".challenge": challenge!, ".host": this };

        const litParts = {
            part: "challenge",
            exportparts: exportParts(["additional-actions", "footer-band"], "challenge"),
        };

        const { tag, variant, importfn } = stage;
        if (importfn) {
            await importfn();
        }

        const props = spread(
            match(variant)
                .with("challenge", () => challengeProps)
                .with("standard", () => ({ ...challengeProps, ...litParts }))
                .with("inspect", () => ({ ...challengeProps, "?promptUser": inspectorOpen }))
                .exhaustive(),
        );

        return staticHTML`<${unsafeStatic(tag)} ${props}></${unsafeStatic(tag)}>`;
    }

    //#endregion

    //#region Render Inspector

    @listen(AKFlowInspectorChangeEvent)
    protected toggleInspector = () => {
        this.inspectorOpen = !this.inspectorOpen;

        const drawer = document.getElementById("flow-drawer");

        if (!drawer) {
            return;
        }

        drawer.classList.toggle("pf-m-expanded", this.inspectorOpen);
        drawer.classList.toggle("pf-m-collapsed", !this.inspectorOpen);
    };

    protected renderInspectorButton() {
        return guard([this.inspectorAvailable, this.inspectorOpen], () => {
            if (!this.inspectorAvailable || this.inspectorOpen) {
                return null;
            }

            return html`<button
                aria-label=${this.inspectorOpen
                    ? msg("Close flow inspector")
                    : msg("Open flow inspector")}
                aria-expanded=${this.inspectorOpen ? "true" : "false"}
                class="inspector-toggle pf-c-button pf-m-primary"
                aria-controls="flow-inspector"
                @click=${this.toggleInspector}
            >
                <i class="fa fa-search-plus" aria-hidden="true"></i>
            </button>`;
        });
    }

    //#endregion

    //#region Render

    protected renderLoading(): TemplateResult {
        return html`<slot class="slotted-content" name="placeholder"></slot>`;
    }

    protected override render(): TemplateResult {
        const { component } = this.challenge || {};

        return html`<ak-locale-select
                part="locale-select"
                exportparts="label:locale-select-label,select:locale-select-select"
                class="pf-m-dark"
            ></ak-locale-select>

            <header class="pf-c-login__header">${this.renderInspectorButton()}</header>
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
                ${this.loading && this.challenge
                    ? html`<ak-loading-overlay></ak-loading-overlay>`
                    : nothing}
                ${component ? until(this.renderChallenge(component)) : this.renderLoading()}
            </main>
            <slot name="footer"></slot>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-executor": FlowExecutor;
    }
}
