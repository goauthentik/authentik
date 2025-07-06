import { pluckErrorDetail } from "#common/errors/network";
import { CaptchaHandler, iframeTemplate } from "#flow/stages/captcha/shared";
import { renderStaticHTMLUnsafe } from "@goauthentik/common/purify";
import { akEmptyState } from "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import { createIFrameHTMLWrapper } from "@goauthentik/elements/utils/iframe";
import { ListenerController } from "@goauthentik/elements/utils/listenerController.js";
import { randomId } from "@goauthentik/elements/utils/randomId";
import "@goauthentik/flow/FormStatic";
import "@goauthentik/flow/components/ak-flow-card.js";
import { BaseStage } from "@goauthentik/flow/stages/base";
import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

export type TokenListener = (token: string) => void;

type Dims = { height: number };

interface IframeCaptchaMessage {
    source?: string;
    context?: string;
    message: "captcha";
    token: string;
}

interface IframeResizeMessage {
    source?: string;
    context?: string;
    message: "resize";
    size: Dims;
}

type IframeMessageEvent = MessageEvent<IframeCaptchaMessage | IframeResizeMessage>;

@customElement("ak-stage-captcha")
export class CaptchaStage extends BaseStage<CaptchaChallenge, CaptchaChallengeResponseRequest> {
    static styles: CSSResult[] = [
        PFBase,
        PFLogin,
        PFForm,
        PFFormControl,
        PFTitle,
        css`
            iframe {
                width: 100%;
                height: 0;
            }
        `,
    ];

    //#region Properties

    @property({ type: Boolean })
    public embedded = false;

    @property()
    public onTokenChange: TokenListener = (token: string) => {
        this.host.submit({ component: "ak-stage-captcha", token });
    };

    @property({ attribute: false })
    public refreshedAt = new Date();

    //#endregion

    //#region State

    @state()
    protected activeHandler: CaptchaHandler | null = null;

    @state()
    protected error: string | null = null;

    #scriptElement?: HTMLScriptElement;
    #captchaFrame?: HTMLIFrameElement;
    #captchaDocumentContainer?: HTMLDivElement;
    #listenController = new ListenerController();

    //#endregion

    //#region Getters

    get captchaDocumentContainer(): HTMLDivElement {
        if (this.#captchaDocumentContainer) {
            return this.#captchaDocumentContainer;
        }

        this.#captchaDocumentContainer = document.createElement("div");
        this.#captchaDocumentContainer.id = `ak-captcha-${randomId()}`;

        return this.#captchaDocumentContainer;
    }

    get captchaFrame(): HTMLIFrameElement {
        if (this.#captchaFrame) {
            return this.#captchaFrame;
        }

        this.#captchaFrame = document.createElement("iframe");
        this.#captchaFrame.src = "about:blank";
        this.#captchaFrame.id = `ak-captcha-${randomId()}`;

        return this.#captchaFrame;
    }

    //#endregion

    //#region Listeners

    #frameResizeListener({ height }: Dims) {
        this.captchaFrame.style.height = `${height}px`;
    }

    // ADR: Did not to put anything into `otherwise` or `exhaustive` here because iframe messages
    // that were not of interest to us also weren't necessarily corrupt or suspicious. For example,
    // during testing Storybook throws a lot of cross-iframe messages that we don't care about.

    #messageListener = ({ data }: IframeMessageEvent) => {
        if (!data) return;

        if (data.source !== "goauthentik.io" || data.context !== "flow-executor") {
            return;
        }

        switch (data.message) {
            case "captcha":
                break;

            default:
                break;
        }

        return match(data)
            .with({ message: "captcha" }, ({ token }) => this.onTokenChange(token))
            .with({ message: "resize" }, ({ size }) => this.#frameResizeListener(size))
            .otherwise(({ message }) => {
                console.debug(`authentik/stages/captcha: Unknown message: ${message}`);
            });
    };

    //#endregion

    //#region g-recaptcha

    async renderGReCaptchaFrame() {
        this.renderFrame(
            html`<div
                class="g-recaptcha ak-captcha-container"
                data-sitekey="${this.challenge.siteKey}"
                data-callback="callback"
            ></div>`,
        );
    }

    async executeGReCaptcha() {
        return grecaptcha.ready(() => {
            grecaptcha.execute(
                grecaptcha.render(this.captchaDocumentContainer, {
                    sitekey: this.challenge.siteKey,
                    callback: this.onTokenChange,
                    size: "invisible",
                }),
            );
        });
    }

    async refreshGReCaptchaFrame() {
        this.captchaFrame.contentWindow?.grecaptcha.reset();
    }

    async refreshGReCaptcha() {
        window.grecaptcha.reset();
        window.grecaptcha.execute();
    }

    //#endregion

    //#region h-captcha

    async renderHCaptchaFrame() {
        this.renderFrame(
            html`<div
                class="h-captcha ak-captcha-container"
                data-sitekey="${this.challenge.siteKey}"
                data-theme="${this.activeTheme ? this.activeTheme : "light"}"
                data-callback="callback"
            ></div> `,
        );
    }

    async executeHCaptcha() {
        return hcaptcha.execute(
            hcaptcha.render(this.captchaDocumentContainer, {
                sitekey: this.challenge.siteKey,
                callback: this.onTokenChange,
                size: "invisible",
            }),
        );
    }

    async refreshHCaptchaFrame() {
        this.captchaFrame.contentWindow?.hcaptcha?.reset();
    }

    async refreshHCaptcha() {
        window.hcaptcha.reset();
        window.hcaptcha.execute();
    }

    //#endregion

    //#region Turnstile

    async renderTurnstileFrame() {
        this.renderFrame(
            html`<div
                class="cf-turnstile ak-captcha-container"
                data-sitekey="${this.challenge.siteKey}"
                data-callback="callback"
            ></div>`,
        );
    }

    async executeTurnstile() {
        return window.turnstile.render(this.captchaDocumentContainer, {
            sitekey: this.challenge.siteKey,
            callback: this.onTokenChange,
        });
    }

    async refreshTurnstileFrame() {
        this.captchaFrame.contentWindow?.turnstile.reset();
    }

    async refreshTurnstile() {
        window.turnstile.reset();
    }

    //#endregion

    #handlers = new Map<string, CaptchaHandler>([
        [
            "grecaptcha",
            {
                interactive: this.renderGReCaptchaFrame,
                execute: this.executeGReCaptcha,
                refreshInteractive: this.refreshGReCaptchaFrame,
                refresh: this.refreshGReCaptcha,
            },
        ],
        [
            "hcaptcha",
            {
                interactive: this.renderHCaptchaFrame,
                execute: this.executeHCaptcha,
                refreshInteractive: this.refreshHCaptchaFrame,
                refresh: this.refreshHCaptcha,
            },
        ],
        [
            "turnstile",
            {
                interactive: this.renderTurnstileFrame,
                refreshInteractive: this.refreshTurnstileFrame,
                execute: this.executeTurnstile,
                refresh: this.refreshTurnstile,
            },
        ],
    ]);

    //#region Render

    async renderFrame(captchaElement: TemplateResult) {
        const { contentDocument } = this.captchaFrame || {};

        if (!contentDocument) {
            console.debug(
                "authentik/stages/captcha: unable to render captcha frame, no contentDocument",
            );

            return;
        }

        contentDocument.open();

        contentDocument.write(
            createIFrameHTMLWrapper(
                renderStaticHTMLUnsafe(iframeTemplate(captchaElement, this.challenge.jsUrl)),
            ),
        );

        contentDocument.close();
    }

    renderBody() {
        if (this.error) {
            return akEmptyState({ icon: "fa-times" }, { heading: this.error });
        }

        if (this.challenge?.interactive) {
            return html`${this.captchaFrame}`;
        }

        return akEmptyState({ loading: true }, { heading: msg("Verifying...") });
    }

    renderMain() {
        return html`<ak-flow-card .challenge=${this.challenge}>
            <form class="pf-c-form">
                <ak-form-static
                    class="pf-c-form__group"
                    userAvatar="${this.challenge.pendingUserAvatar}"
                    user=${this.challenge.pendingUser}
                >
                    <div slot="link">
                        <a href="${ifDefined(this.challenge.flowInfo?.cancelUrl)}"
                            >${msg("Not you?")}</a
                        >
                    </div>
                </ak-form-static>
                ${this.renderBody()}
            </form>
        </ak-flow-card>`;
    }

    render() {
        if (!this.challenge) {
            return this.embedded ? nothing : akEmptyState({ loading: true });
        }

        if (!this.embedded) {
            return this.renderMain();
        }

        return this.challenge.interactive ? this.renderBody() : nothing;
    }

    //#endregion;

    //#region Lifecycle

    public connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener("message", this.#messageListener, {
            signal: this.#listenController.signal,
        });
    }

    public disconnectedCallback(): void {
        this.#listenController.abort();

        if (!this.challenge?.interactive) {
            if (document.body.contains(this.captchaDocumentContainer)) {
                document.body.removeChild(this.captchaDocumentContainer);
            }
        }

        super.disconnectedCallback();
    }

    //#endregion

    public firstUpdated(changedProperties: PropertyValues<this>) {
        if (!(changedProperties.has("challenge") && typeof this.challenge !== "undefined")) {
            return;
        }

        const loadListener = async () => {
            console.debug("authentik/stages/captcha: script loaded");

            let lastError: unknown;
            let found = false;

            for (const [name, handler] of this.#handlers) {
                if (!Object.hasOwn(window, name)) {
                    continue;
                }

                console.debug(`authentik/stages/captcha: trying handler ${name}`);

                const runner = this.challenge.interactive ? handler.interactive : handler.execute;

                try {
                    await runner.apply(this);

                    console.debug(`authentik/stages/captcha[${name}]: handler succeeded`);

                    found = true;
                    this.activeHandler = handler;

                    break;
                } catch (error) {
                    console.debug(`authentik/stages/captcha[${name}]: handler failed`);
                    console.debug(error);

                    lastError = error;
                }
            }

            this.error = found ? null : pluckErrorDetail(lastError, "Unspecified error");
        };

        const scriptElement = document.createElement("script");

        scriptElement.src = this.challenge.jsUrl;
        scriptElement.async = true;
        scriptElement.defer = true;
        scriptElement.onload = loadListener;

        this.#scriptElement?.remove();

        this.#scriptElement = document.head.appendChild(scriptElement);

        if (!this.challenge.interactive) {
            document.body.appendChild(this.captchaDocumentContainer);
        }
    }

    public updated(changedProperties: PropertyValues<this>) {
        if (!changedProperties.has("refreshedAt") || !this.challenge) {
            return;
        }

        console.debug("authentik/stages/captcha: refresh triggered");

        const handler = this.challenge.interactive
            ? this.activeHandler?.refreshInteractive
            : this.activeHandler?.refresh;

        handler?.apply(this);
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha": CaptchaStage;
    }
}
