import "#flow/stages/authenticator_webauthn/WebAuthnAuthenticatorRegisterStage";
import "#elements/LoadingOverlay";
import "#elements/locale/ak-locale-select";
import "#flow/components/ak-brand-footer";
import "#flow/components/ak-flow-card";
import "#flow/FlowInspectorButton";

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

import { AKFlowAdvanceEvent } from "#flow/events";
import { BaseStage, StageHost, SubmitOptions } from "#flow/stages/base";

import { ConsoleLogger } from "#logger/browser";

import {
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
import { CSSResult, html, nothing, PropertyValues, render, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeHTML } from "lit/directives/unsafe-html.js";
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

    @property({ type: String, attribute: "data-layout", useDefault: true, reflect: true })
    public layout: FlowLayoutEnum = FlowExecutor.DefaultLayout;

    //#endregion

    //#region State

    #logger = ConsoleLogger.prefix("flow-executor");

    #api: FlowsApi;

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

        this.#api = new FlowsApi(DEFAULT_CONFIG);

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

        if (
            (changedProperties.has("flowInfo") || changedProperties.has("activeTheme")) &&
            this.flowInfo
        ) {
            this.#synchronizeFlowInfo();
        }

        const previous = Array.from(this.children).find((el) =>
            el.matches('[slot="slotted-dialog"]'),
        );
        (previous as Element | undefined)?.remove();

        if (this.challenge) {
            this.renderChallenge(this.challenge);
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

        return this.#api
            .flowsExecutorSolve({
                flowSlug: this.flowSlug,
                query: window.location.search.substring(1),
                flowChallengeResponseRequest: payload,
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
        const { component } = challenge;

        const stage = stages.get(component);

        // The special cases!
        if (!stage) {
            if (component === "xak-flow-shell") {
                return html`${unsafeHTML((challenge as ShellChallenge).body)}`;
            }
            return html`Invalid native challenge element`;
        }

        const challengeProps: LitPropertyRecord<BaseStage<NonNullable<typeof challenge>, unknown>> =
            {
                ".challenge": challenge!,
                ".host": this,
            };

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
                .exhaustive(),
        );

        render(
            staticHTML`<${unsafeStatic(tag)} ${props} slot="slotted-dialog"></${unsafeStatic(tag)}>`,
            this,
        );
    }

    //#endregion

    //#region Render

    protected override render(): TemplateResult {
        const { component } = this.challenge || {};

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
                ${this.loading && this.challenge
                    ? html`<ak-loading-overlay></ak-loading-overlay>`
                    : nothing}
                ${component
                    ? html`<div part="slotted-dialog">
                          <slot name="slotted-dialog" value=${component}></slot>
                      </div>`
                    : html`<slot class="slotted-content" name="placeholder"></slot>`}
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
