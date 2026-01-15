import "#flow/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import "#elements/LoadingOverlay";
import "#elements/locale/ak-locale-select";
import "#flow/components/ak-brand-footer";
import "#flow/components/ak-flow-card";
import "#flow/sources/apple/AppleLoginInit";
import "#flow/sources/plex/PlexLoginInit";
import "#flow/sources/telegram/TelegramLogin";
import "#flow/stages/FlowErrorStage";
import "#flow/stages/FlowFrameStage";
import "#flow/stages/RedirectStage";

import Styles from "./FlowExecutor.css" with { type: "bundled-text" };

import { DEFAULT_CONFIG } from "#common/api/config";
import { pluckErrorDetail } from "#common/errors/network";
import { globalAK } from "#common/global";
import { configureSentry } from "#common/sentry/index";
import { applyBackgroundImageProperty } from "#common/theme";
import { AKSessionAuthenticatedEvent } from "#common/ws/events";
import { WebsocketClient } from "#common/ws/WebSocketClient";

import { listen } from "#elements/decorators/listen";
import { Interface } from "#elements/Interface";
import { WithBrandConfig } from "#elements/mixins/branding";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { LitPropertyRecord } from "#elements/types";
import { exportParts } from "#elements/utils/attributes";
import { ThemedImage } from "#elements/utils/images";

import { AKFlowAdvanceEvent, AKFlowInspectorChangeEvent } from "#flow/events";
import { BaseStage, StageHost, SubmitOptions } from "#flow/stages/base";

import {
    CapabilitiesEnum,
    ChallengeTypes,
    ContextualFlowInfo,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowLayoutEnum,
    FlowsApi,
    ShellChallenge,
} from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";

import PFBackgroundImage from "@patternfly/patternfly/components/BackgroundImage/background-image.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";

@customElement("ak-flow-executor")
export class FlowExecutor
    extends WithCapabilitiesConfig(WithBrandConfig(Interface))
    implements StageHost
{
    static readonly DefaultLayout: FlowLayoutEnum =
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

    #challenge: ChallengeTypes | null = null;

    @property({ attribute: false })
    public set challenge(value: ChallengeTypes | null) {
        const previousValue = this.#challenge;
        const previousTitle = previousValue?.flowInfo?.title;
        const nextTitle = value?.flowInfo?.title;

        this.#challenge = value;

        if (!nextTitle) {
            document.title = this.brandingTitle;
        } else if (nextTitle !== previousTitle) {
            document.title = `${nextTitle} - ${this.brandingTitle}`;
        }

        this.requestUpdate("challenge", previousValue);
    }

    public get challenge(): ChallengeTypes | null {
        return this.#challenge;
    }

    @property({ type: Boolean })
    public loading = false;

    //#endregion

    //#region State

    #inspectorLoaded = false;

    @property({ type: Boolean })
    public inspectorOpen?: boolean;

    @property({ type: Boolean })
    public inspectorAvailable?: boolean;

    @property({ type: String, attribute: "data-layout", useDefault: true, reflect: true })
    public layout: FlowLayoutEnum = FlowExecutor.DefaultLayout;

    @state()
    public flowInfo?: ContextualFlowInfo;

    //#endregion

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

    protected refresh = () => {
        this.loading = true;

        return new FlowsApi(DEFAULT_CONFIG)
            .flowsExecutorGet({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
            })
            .then((challenge) => {
                this.challenge = challenge;

                if (this.challenge.flowInfo) {
                    this.flowInfo = this.challenge.flowInfo;
                }
            })
            .catch((error) => {
                const challenge: FlowErrorChallenge = {
                    component: "ak-stage-flow-error",
                    error: pluckErrorDetail(error),
                    requestId: "",
                };

                this.challenge = challenge as ChallengeTypes;
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

        if (changedProperties.has("challenge") && this.challenge?.flowInfo) {
            this.layout = this.challenge?.flowInfo?.layout || FlowExecutor.DefaultLayout;
        }

        if (changedProperties.has("flowInfo") && this.flowInfo) {
            applyBackgroundImageProperty(this.flowInfo.background);
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

                if (this.challenge.flowInfo) {
                    this.flowInfo = this.challenge.flowInfo;
                }

                return !this.challenge.responseErrors;
            })
            .catch((error: unknown) => {
                const challenge: FlowErrorChallenge = {
                    component: "ak-stage-flow-error",
                    error: pluckErrorDetail(error),
                    requestId: "",
                };

                this.challenge = challenge as ChallengeTypes;
                return false;
            })
            .finally(() => {
                this.loading = false;
            });
    };

    //#region Render Challenge

    async renderChallenge(component: ChallengeTypes["component"]): Promise<TemplateResult> {
        const { challenge, inspectorOpen } = this;

        const stageProps: LitPropertyRecord<BaseStage<NonNullable<typeof challenge>, unknown>> = {
            ".challenge": challenge!,
            ".host": this,
        };

        const props = {
            ...stageProps,
            part: "challenge",
            exportparts: exportParts(["additional-actions", "footer-band"], "challenge"),
        };

        switch (component) {
            case "ak-stage-access-denied":
                await import("#flow/stages/access_denied/AccessDeniedStage");
                return html`<ak-stage-access-denied ${spread(props)}></ak-stage-access-denied>`;
            case "ak-stage-identification":
                await import("#flow/stages/identification/IdentificationStage");
                return html`<ak-stage-identification ${spread(props)}></ak-stage-identification>`;
            case "ak-stage-password":
                await import("#flow/stages/password/PasswordStage");
                return html`<ak-stage-password ${spread(props)}></ak-stage-password>`;
            case "ak-stage-captcha":
                await import("#flow/stages/captcha/CaptchaStage");
                return html`<ak-stage-captcha ${spread(props)}></ak-stage-captcha>`;
            case "ak-stage-consent":
                await import("#flow/stages/consent/ConsentStage");
                return html`<ak-stage-consent ${spread(props)}></ak-stage-consent>`;
            case "ak-stage-dummy":
                await import("#flow/stages/dummy/DummyStage");
                return html`<ak-stage-dummy ${spread(props)}></ak-stage-dummy>`;
            case "ak-stage-email":
                await import("#flow/stages/email/EmailStage");
                return html`<ak-stage-email ${spread(props)}></ak-stage-email>`;
            case "ak-stage-autosubmit":
                await import("#flow/stages/autosubmit/AutosubmitStage");
                return html`<ak-stage-autosubmit ${spread(props)}></ak-stage-autosubmit>`;
            case "ak-stage-prompt":
                await import("#flow/stages/prompt/PromptStage");
                return html`<ak-stage-prompt ${spread(props)}></ak-stage-prompt>`;
            case "ak-stage-authenticator-totp":
                await import("#flow/stages/authenticator_totp/AuthenticatorTOTPStage");
                return html`<ak-stage-authenticator-totp
                    ${spread(props)}
                ></ak-stage-authenticator-totp>`;
            case "ak-stage-authenticator-duo":
                await import("#flow/stages/authenticator_duo/AuthenticatorDuoStage");
                return html`<ak-stage-authenticator-duo
                    ${spread(props)}
                ></ak-stage-authenticator-duo>`;
            case "ak-stage-authenticator-static":
                await import("#flow/stages/authenticator_static/AuthenticatorStaticStage");
                return html`<ak-stage-authenticator-static
                    ${spread(props)}
                ></ak-stage-authenticator-static>`;
            case "ak-stage-authenticator-webauthn":
                return html`<ak-stage-authenticator-webauthn
                    ${spread(props)}
                ></ak-stage-authenticator-webauthn>`;
            case "ak-stage-authenticator-email":
                await import("#flow/stages/authenticator_email/AuthenticatorEmailStage");
                return html`<ak-stage-authenticator-email
                    ${spread(props)}
                ></ak-stage-authenticator-email>`;
            case "ak-stage-authenticator-sms":
                await import("#flow/stages/authenticator_sms/AuthenticatorSMSStage");
                return html`<ak-stage-authenticator-sms
                    ${spread(props)}
                ></ak-stage-authenticator-sms>`;
            case "ak-stage-authenticator-validate":
                await import("#flow/stages/authenticator_validate/AuthenticatorValidateStage");
                return html`<ak-stage-authenticator-validate
                    ${spread(props)}
                ></ak-stage-authenticator-validate>`;
            case "ak-stage-user-login":
                await import("#flow/stages/user_login/UserLoginStage");
                return html`<ak-stage-user-login
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-user-login>`;
            case "ak-stage-endpoint-agent":
                await import("#flow/stages/endpoint/agent/EndpointAgentStage");
                return html`<ak-stage-endpoint-agent
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></ak-stage-endpoint-agent>`;
            // Sources
            case "ak-source-plex":
                return html`<ak-flow-source-plex ${spread(props)}></ak-flow-source-plex>`;
            case "ak-source-oauth-apple":
                return html`<ak-flow-source-oauth-apple
                    ${spread(props)}
                ></ak-flow-source-oauth-apple>`;
            case "ak-source-telegram":
                return html`<ak-flow-source-telegram ${spread(props)}></ak-flow-source-telegram>`;
            // Providers
            case "ak-provider-oauth2-device-code":
                await import("#flow/providers/oauth2/DeviceCode");
                return html`<ak-flow-provider-oauth2-code
                    ${spread(props)}
                ></ak-flow-provider-oauth2-code>`;
            case "ak-provider-oauth2-device-code-finish":
                await import("#flow/providers/oauth2/DeviceCodeFinish");
                return html`<ak-flow-provider-oauth2-code-finish
                    ${spread(props)}
                ></ak-flow-provider-oauth2-code-finish>`;
            case "ak-stage-session-end":
                await import("#flow/providers/SessionEnd");
                return html`<ak-stage-session-end ${spread(props)}></ak-stage-session-end>`;
            case "ak-provider-saml-native-logout":
                await import("#flow/providers/saml/NativeLogoutStage");
                return html`<ak-provider-saml-native-logout
                    ${spread(props)}
                ></ak-provider-saml-native-logout>`;
            case "ak-provider-iframe-logout":
                await import("#flow/providers/IFrameLogoutStage");
                return html`<ak-provider-iframe-logout
                    ${spread(props)}
                ></ak-provider-iframe-logout>`;
            // Internal stages
            case "ak-stage-flow-error":
                return html`<ak-stage-flow-error ${spread(props)}></ak-stage-flow-error>`;
            case "xak-flow-redirect":
                return html`<ak-stage-redirect ${spread(props)} ?promptUser=${inspectorOpen}>
                </ak-stage-redirect>`;
            case "xak-flow-shell":
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case "xak-flow-frame":
                return html`<xak-flow-frame
                    .host=${this}
                    .challenge=${challenge}
                ></xak-flow-frame>`;
            default:
                return html`Invalid native challenge element`;
        }
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

    public override render(): TemplateResult {
        const { component } = this.challenge || {};

        return html`<ak-locale-select
                part="locale-select"
                exportparts="label:locale-select-label,select:locale-select-select"
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
