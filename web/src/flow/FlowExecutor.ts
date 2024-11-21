import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_FLOW_ADVANCE,
    EVENT_FLOW_INSPECTOR_TOGGLE,
    TITLE_DEFAULT,
} from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import { configureSentry } from "@goauthentik/common/sentry";
import { WebsocketClient } from "@goauthentik/common/ws";
import { Interface } from "@goauthentik/elements/Interface";
import "@goauthentik/elements/LoadingOverlay";
import "@goauthentik/elements/ak-locale-context";
import { DefaultBrand } from "@goauthentik/elements/sidebar/SidebarBrand";
import { themeImage } from "@goauthentik/elements/utils/images";
import "@goauthentik/flow/components/ak-brand-footer";
import "@goauthentik/flow/sources/apple/AppleLoginInit";
import "@goauthentik/flow/sources/plex/PlexLoginInit";
import "@goauthentik/flow/stages/FlowErrorStage";
import "@goauthentik/flow/stages/FlowFrameStage";
import "@goauthentik/flow/stages/RedirectStage";
import { StageHost, SubmitOptions } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
import { until } from "lit/directives/until.js";
import { html as staticHtml, unsafeStatic } from "lit/static-html.js";

import PFBackgroundImage from "@patternfly/patternfly/components/BackgroundImage/background-image.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFList from "@patternfly/patternfly/components/List/list.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import {
    CapabilitiesEnum,
    ChallengeTypes,
    ContextualFlowInfo,
    FetchError,
    FlowChallengeResponseRequest,
    FlowErrorChallenge,
    FlowLayoutEnum,
    FlowsApi,
    ResponseError,
    ShellChallenge,
    UiThemeEnum,
} from "@goauthentik/api";

type StageRenderer = {
    // Provide the lit-element tag if it's different from the challenge.component name
    tag?: string;
    // Provide a dynamic import whenever possible; otherwise, make sure you include it in the
    // build-time imports above.
    import?: () => Promise<unknown>;
};
type StageRenderers = { [key: string]: StageRenderer };

// authentik's standard stages and the Lit components that handle them. A "standard stage" conforms
// to an API that takes two properties:
// `.host=${host: StageHost} .challenge=${challenge: ChallengeTypes}`
// Exceptions are handled in a switch/case statement below the renderer for these.

// All of that `async () => await import("@goauthentik/flow/...")` boilerplate cannot be abstracted
// away because [import is not a function](https://v8.dev/features/dynamic-import), it is a
// _statement_, and its contents are statically analyzed by bundlers, compilers, and the V8
// interpreter.

// Prettier ignore to keep the table looking like a table:
// prettier-ignore
const allStages: StageRenderers = {
    "ak-stage-access-denied": { import: async () => await import("@goauthentik/flow/stages/access_denied/AccessDeniedStage") },
    "ak-stage-identification": { import: async () => await import("@goauthentik/flow/stages/identification/IdentificationStage") },
    "ak-stage-password": { import: async () => await import("@goauthentik/flow/stages/password/PasswordStage") },
    "ak-stage-captcha": { import: async () => await import("@goauthentik/flow/stages/captcha/CaptchaStage") },
    "ak-stage-consent": { import: async () => await import("@goauthentik/flow/stages/consent/ConsentStage") },
    "ak-stage-dummy": { import: async () => await import("@goauthentik/flow/stages/dummy/DummyStage") },
    "ak-stage-email": { import: async () => await import("@goauthentik/flow/stages/email/EmailStage") },
    "ak-stage-autosubmit": { import: async () => await import("@goauthentik/flow/stages/autosubmit/AutosubmitStage") },
    "ak-stage-prompt": { import: async () => await import("@goauthentik/flow/stages/prompt/PromptStage") },
    "ak-stage-authenticator-totp": { import: async () => await import("@goauthentik/flow/stages/authenticator_totp/AuthenticatorTOTPStage") },
    "ak-stage-authenticator-duo": { import: async () => await import("@goauthentik/flow/stages/authenticator_duo/AuthenticatorDuoStage") },
    "ak-stage-authenticator-static": { import: async () => await import("@goauthentik/flow/stages/authenticator_static/AuthenticatorStaticStage") },
    "ak-stage-authenticator-webauthn": { },
    "ak-stage-authenticator-sms": { import: async () => await import("@goauthentik/flow/stages/authenticator_sms/AuthenticatorSMSStage") },
    "ak-stage-authenticator-validate": { import: async () => await import("@goauthentik/flow/stages/authenticator_validate/AuthenticatorValidateStage") },
    "ak-stage-user-login": { import: async () => await import("@goauthentik/flow/stages/user_login/UserLoginStage") },
    "ak-source-plex": { tag: "ak-flow-source-plex" },
    "ak-source-oauth-apple": { tag: "ak-flow-source-oauth-apple" },
    "ak-provider-oauth2-device-code": { tag: "ak-flow-provider-oauth2-code", import: async () => await import("@goauthentik/flow/providers/oauth2/DeviceCode") },
    "ak-provider-oauth2-device-code-finish": { tag: "ak-flow-provider-oauth2-code-finish", import: async () => await import("@goauthentik/flow/providers/oauth2/DeviceCodeFinish") },
    "ak-stage-session-end": { import: async () => await import("@goauthentik/flow/providers/SessionEnd") },
    "ak-stage-flow-error": { },
} as const;

@customElement("ak-flow-executor")
export class FlowExecutor extends Interface implements StageHost {
    @property()
    flowSlug: string = window.location.pathname.split("/")[3];

    private _challenge?: ChallengeTypes;

    @property({ attribute: false })
    set challenge(value: ChallengeTypes | undefined) {
        this._challenge = value;
        if (value?.flowInfo?.title) {
            document.title = `${value.flowInfo?.title} - ${this.brand?.brandingTitle}`;
        } else {
            document.title = this.brand?.brandingTitle || TITLE_DEFAULT;
        }
        this.requestUpdate();
    }

    get challenge(): ChallengeTypes | undefined {
        return this._challenge;
    }

    @property({ type: Boolean })
    loading = false;

    @state()
    inspectorOpen = false;

    @state()
    flowInfo?: ContextualFlowInfo;

    ws: WebsocketClient;

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFDrawer, PFButton, PFTitle, PFList, PFBackgroundImage].concat(css`
            :host {
                --pf-c-login__main-body--PaddingBottom: var(--pf-global--spacer--2xl);
            }
            .pf-c-background-image::before {
                --pf-c-background-image--BackgroundImage: var(--ak-flow-background);
                --pf-c-background-image--BackgroundImage-2x: var(--ak-flow-background);
                --pf-c-background-image--BackgroundImage--sm: var(--ak-flow-background);
                --pf-c-background-image--BackgroundImage--sm-2x: var(--ak-flow-background);
                --pf-c-background-image--BackgroundImage--lg: var(--ak-flow-background);
            }
            .ak-hidden {
                display: none;
            }
            :host {
                position: relative;
            }
            .pf-c-drawer__content {
                background-color: transparent;
            }
            /* layouts */
            @media (min-height: 60rem) {
                .pf-c-login.stacked .pf-c-login__main {
                    margin-top: 13rem;
                }
            }
            .pf-c-login__container.content-right {
                grid-template-areas:
                    "header main"
                    "footer main"
                    ". main";
            }
            .pf-c-login.sidebar_left {
                justify-content: flex-start;
                padding-top: 0;
                padding-bottom: 0;
            }
            .pf-c-login.sidebar_left .ak-login-container,
            .pf-c-login.sidebar_right .ak-login-container {
                height: 100vh;
                background-color: var(--pf-c-login__main--BackgroundColor);
                padding-left: var(--pf-global--spacer--lg);
                padding-right: var(--pf-global--spacer--lg);
            }
            .pf-c-login.sidebar_left .pf-c-list,
            .pf-c-login.sidebar_right .pf-c-list {
                color: #000;
            }
            .pf-c-login.sidebar_right {
                justify-content: flex-end;
                padding-top: 0;
                padding-bottom: 0;
            }
            :host([theme="dark"]) .pf-c-login.sidebar_left .ak-login-container,
            :host([theme="dark"]) .pf-c-login.sidebar_right .ak-login-container {
                background-color: var(--ak-dark-background);
            }
            :host([theme="dark"]) .pf-c-login.sidebar_left .pf-c-list,
            :host([theme="dark"]) .pf-c-login.sidebar_right .pf-c-list {
                color: var(--ak-dark-foreground);
            }
            .pf-c-brand {
                padding-top: calc(
                    var(--pf-c-login__main-footer-links--PaddingTop) +
                        var(--pf-c-login__main-footer-links--PaddingBottom) +
                        var(--pf-c-login__main-body--PaddingBottom)
                );
                max-height: 9rem;
            }
            .ak-brand {
                display: flex;
                justify-content: center;
            }
            .ak-brand img {
                padding: 0 2rem;
                max-height: inherit;
            }
        `);
    }

    constructor() {
        super();
        this.ws = new WebsocketClient();
        if (window.location.search.includes("inspector")) {
            this.inspectorOpen = true;
        }
        this.addEventListener(EVENT_FLOW_INSPECTOR_TOGGLE, () => {
            this.inspectorOpen = !this.inspectorOpen;
        });
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

    async getTheme(): Promise<UiThemeEnum> {
        return globalAK()?.brand.uiTheme || UiThemeEnum.Automatic;
    }

    async submit(
        payload?: FlowChallengeResponseRequest,
        options?: SubmitOptions,
    ): Promise<boolean> {
        if (!payload) return Promise.reject();
        if (!this.challenge) return Promise.reject();
        // @ts-expect-error
        payload.component = this.challenge.component;
        if (!options?.invisible) {
            this.loading = true;
        }
        try {
            const challenge = await new FlowsApi(DEFAULT_CONFIG).flowsExecutorSolve({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
                flowChallengeResponseRequest: payload,
            });
            if (this.inspectorOpen) {
                window.dispatchEvent(
                    new CustomEvent(EVENT_FLOW_ADVANCE, {
                        bubbles: true,
                        composed: true,
                    }),
                );
            }
            this.challenge = challenge;
            if (this.challenge.flowInfo) {
                this.flowInfo = this.challenge.flowInfo;
            }
            return !this.challenge.responseErrors;
        } catch (exc: unknown) {
            this.errorMessage(exc as Error | ResponseError | FetchError);
            return false;
        } finally {
            this.loading = false;
        }
    }

    async firstUpdated(): Promise<void> {
        configureSentry();
        if (this.config?.capabilities.includes(CapabilitiesEnum.CanDebug)) {
            this.inspectorOpen = true;
        }
        this.loading = true;
        try {
            const challenge = await new FlowsApi(DEFAULT_CONFIG).flowsExecutorGet({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
            });
            if (this.inspectorOpen) {
                window.dispatchEvent(
                    new CustomEvent(EVENT_FLOW_ADVANCE, {
                        bubbles: true,
                        composed: true,
                    }),
                );
            }
            this.challenge = challenge;
            if (this.challenge.flowInfo) {
                this.flowInfo = this.challenge.flowInfo;
            }
        } catch (exc: unknown) {
            // Catch JSON or Update errors
            this.errorMessage(exc as Error | ResponseError | FetchError);
        } finally {
            this.loading = false;
        }
    }

    async errorMessage(error: Error | ResponseError | FetchError): Promise<void> {
        let body = "";
        if (error instanceof FetchError) {
            body = msg("Request failed. Please try again later.");
        } else if (error instanceof ResponseError) {
            body = await error.response.text();
        } else if (error instanceof Error) {
            body = error.message;
        }
        const challenge: FlowErrorChallenge = {
            component: "ak-stage-flow-error",
            error: body,
            requestId: "",
        };
        this.challenge = challenge as ChallengeTypes;
    }

    setShadowStyles(value: ContextualFlowInfo) {
        if (!value) {
            return;
        }
        this.shadowRoot
            ?.querySelectorAll<HTMLDivElement>(".pf-c-background-image")
            .forEach((bg) => {
                bg.style.setProperty("--ak-flow-background", `url('${value?.background}')`);
            });
    }

    // DOM post-processing has to happen after the render.
    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("flowInfo") && this.flowInfo !== undefined) {
            this.setShadowStyles(this.flowInfo);
        }
    }

    async renderChallenge(): Promise<TemplateResult> {
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        const stage = allStages[this.challenge.component];
        if (stage) {
            if (stage.import) {
                await stage.import();
            }
            const tag = stage.tag ?? this.challenge.component;
            // Prettier doesn't know what `staticHTML` is, will try to format it by
            // prettier-ignore
            return staticHtml`<${unsafeStatic(tag)}
                .host=${this as StageHost}
                .challenge=${this.challenge}
            ></${unsafeStatic(tag)}>`;
        }

        switch (this.challenge?.component) {
            case "xak-flow-redirect":
                return html`<ak-stage-redirect
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                    ?promptUser=${this.inspectorOpen}
                >
                </ak-stage-redirect>`;
            case "xak-flow-shell":
                return html`${unsafeHTML((this.challenge as ShellChallenge).body)}`;
            case "xak-flow-frame":
                return html`<xak-flow-frame
                    .host=${this as StageHost}
                    .challenge=${this.challenge}
                ></xak-flow-frame>`;
            default:
                return html`Invalid native challenge element`;
        }
    }

    async renderInspector() {
        if (!this.inspectorOpen) {
            return nothing;
        }
        await import("@goauthentik/flow/FlowInspector");
        return html`<ak-flow-inspector
            class="pf-c-drawer__panel pf-m-width-33"
        ></ak-flow-inspector>`;
    }

    getLayout(): string {
        const prefilledFlow = globalAK()?.flow?.layout || FlowLayoutEnum.Stacked;
        if (this.challenge) {
            return this.challenge?.flowInfo?.layout || prefilledFlow;
        }
        return prefilledFlow;
    }

    getLayoutClass(): string {
        const layout = this.getLayout();
        switch (layout) {
            case FlowLayoutEnum.ContentLeft:
                return "pf-c-login__container";
            case FlowLayoutEnum.ContentRight:
                return "pf-c-login__container content-right";
            case FlowLayoutEnum.Stacked:
            default:
                return "ak-login-container";
        }
    }

    render(): TemplateResult {
        return html` <ak-locale-context>
            <div class="pf-c-background-image"></div>
            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer ${this.inspectorOpen ? "pf-m-expanded" : "pf-m-collapsed"}">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                <div class="pf-c-login ${this.getLayout()}">
                                    <div class="${this.getLayoutClass()}">
                                        <div class="pf-c-login__main">
                                            ${this.loading && this.challenge
                                                ? html`<ak-loading-overlay></ak-loading-overlay>`
                                                : nothing}
                                            <div
                                                class="pf-c-login__main-header pf-c-brand ak-brand"
                                            >
                                                <img
                                                    src="${themeImage(
                                                        this.brand?.brandingLogo ??
                                                            globalAK()?.brand.brandingLogo ??
                                                            DefaultBrand.brandingLogo,
                                                    )}"
                                                    alt="authentik Logo"
                                                />
                                            </div>
                                            ${until(this.renderChallenge())}
                                        </div>
                                        <footer class="pf-c-login__footer">
                                            <ak-brand-links
                                                .links=${this.brand?.uiFooterLinks ?? []}
                                            ></ak-brand-links>
                                        </footer>
                                    </div>
                                </div>
                            </div>
                        </div>
                        ${until(this.renderInspector())}
                    </div>
                </div>
            </div>
        </ak-locale-context>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-flow-executor": FlowExecutor;
    }
}
