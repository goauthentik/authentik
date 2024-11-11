///<reference types="@hcaptcha/types"/>
import { renderStatic } from "@goauthentik/common/purify";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import { randomId } from "@goauthentik/elements/utils/randomId";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";
import type { TurnstileObject } from "turnstile-types";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

interface TurnstileWindow extends Window {
    turnstile: TurnstileObject;
}
type TokenHandler = (token: string) => void;

@customElement("ak-stage-captcha")
export class CaptchaStage extends BaseStage<CaptchaChallenge, CaptchaChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFLogin,
            PFForm,
            PFFormControl,
            PFTitle,
            css`
                iframe {
                    width: 100%;
                    height: 73px; /* tmp */
                }
            `,
        ];
    }

    handlers = [this.handleGReCaptcha, this.handleHCaptcha, this.handleTurnstile];

    @state()
    error?: string;

    @state()
    captchaFrame: HTMLIFrameElement;

    @state()
    captchaDocumentContainer: HTMLDivElement;

    @state()
    scriptElement?: HTMLScriptElement;

    @property({ type: Boolean })
    embedded = false;

    @property()
    onTokenChange: TokenHandler = (token: string) => {
        this.host.submit({ component: "ak-stage-captcha", token });
    };

    constructor() {
        super();
        this.captchaFrame = document.createElement("iframe");
        this.captchaFrame.src = "about:blank";
        this.captchaFrame.id = `ak-captcha-${randomId()}`;

        this.captchaDocumentContainer = document.createElement("div");
        this.captchaDocumentContainer.id = `ak-captcha-${randomId()}`;
        this.messageCallback = this.messageCallback.bind(this);
    }

    connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener("message", this.messageCallback);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener("message", this.messageCallback);
        if (!this.challenge.interactive) {
            document.removeChild(this.captchaDocumentContainer);
        }
    }

    messageCallback(
        ev: MessageEvent<{
            source?: string;
            context?: string;
            message: string;
            token: string;
        }>,
    ) {
        const msg = ev.data;
        if (msg.source !== "goauthentik.io" || msg.context !== "flow-executor") {
            return;
        }
        if (msg.message !== "captcha") {
            return;
        }
        this.onTokenChange(msg.token);
    }

    async renderFrame(captchaElement: TemplateResult) {
        this.captchaFrame.contentWindow?.document.open();
        this.captchaFrame.contentWindow?.document.write(
            await renderStatic(
                html`<!doctype html>
                    <html>
                        <body style="display:flex;flex-direction:row;justify-content:center;">
                            ${captchaElement}
                            <script src=${this.challenge.jsUrl}></script>
                            <script>
                                function callback(token) {
                                    window.parent.postMessage({
                                        message: "captcha",
                                        source: "goauthentik.io",
                                        context: "flow-executor",
                                        token: token,
                                    });
                                }
                            </script>
                        </body>
                    </html>`,
            ),
        );
        this.captchaFrame.contentWindow?.document.close();
    }

    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("challenge") && this.challenge !== undefined) {
            this.scriptElement = document.createElement("script");
            this.scriptElement.src = this.challenge.jsUrl;
            this.scriptElement.async = true;
            this.scriptElement.defer = true;
            this.scriptElement.dataset.akCaptchaScript = "true";
            this.scriptElement.onload = async () => {
                console.debug("authentik/stages/captcha: script loaded");
                let found = false;
                let lastError = undefined;
                this.handlers.forEach(async (handler) => {
                    let handlerFound = false;
                    try {
                        console.debug(`authentik/stages/captcha[${handler.name}]: trying handler`);
                        handlerFound = await handler.apply(this);
                        if (handlerFound) {
                            console.debug(
                                `authentik/stages/captcha[${handler.name}]: handler succeeded`,
                            );
                            found = true;
                        }
                    } catch (exc) {
                        console.debug(
                            `authentik/stages/captcha[${handler.name}]: handler failed: ${exc}`,
                        );
                        if (handlerFound) {
                            lastError = exc;
                        }
                    }
                });
                if (!found && lastError) {
                    this.error = (lastError as Error).toString();
                }
            };
            document.head
                .querySelectorAll("[data-ak-captcha-script=true]")
                .forEach((el) => el.remove());
            document.head.appendChild(this.scriptElement);
            if (!this.challenge.interactive) {
                document.appendChild(this.captchaDocumentContainer);
            }
        }
    }

    async handleGReCaptcha(): Promise<boolean> {
        if (!Object.hasOwn(window, "grecaptcha")) {
            return false;
        }
        if (this.challenge.interactive) {
            this.renderFrame(
                html`<div
                    class="g-recaptcha"
                    data-sitekey="${this.challenge.siteKey}"
                    data-callback="callback"
                ></div>`,
            );
        } else {
            grecaptcha.ready(() => {
                const captchaId = grecaptcha.render(this.captchaDocumentContainer, {
                    sitekey: this.challenge.siteKey,
                    callback: this.onTokenChange,
                    size: "invisible",
                });
                grecaptcha.execute(captchaId);
            });
        }
        return true;
    }

    async handleHCaptcha(): Promise<boolean> {
        if (!Object.hasOwn(window, "hcaptcha")) {
            return false;
        }
        if (this.challenge.interactive) {
            this.renderFrame(
                html`<div
                    class="h-captcha"
                    data-sitekey="${this.challenge.siteKey}"
                    data-theme="${this.activeTheme ? this.activeTheme : "light"}"
                    data-callback="callback"
                ></div> `,
            );
        } else {
            const captchaId = hcaptcha.render(this.captchaDocumentContainer, {
                sitekey: this.challenge.siteKey,
                callback: this.onTokenChange,
                size: "invisible",
            });
            hcaptcha.execute(captchaId);
        }
        return true;
    }

    async handleTurnstile(): Promise<boolean> {
        if (!Object.hasOwn(window, "turnstile")) {
            return false;
        }
        if (this.challenge.interactive) {
            this.renderFrame(
                html`<div
                    class="cf-turnstile"
                    data-sitekey="${this.challenge.siteKey}"
                    data-callback="callback"
                ></div>`,
            );
        } else {
            (window as unknown as TurnstileWindow).turnstile.render(this.captchaDocumentContainer, {
                sitekey: this.challenge.siteKey,
                callback: this.onTokenChange,
            });
        }
        return true;
    }

    renderBody() {
        if (this.error) {
            return html`<ak-empty-state icon="fa-times" header=${this.error}> </ak-empty-state>`;
        }
        if (this.challenge.interactive) {
            return html`${this.captchaFrame}`;
        }
        return html`<ak-empty-state loading header=${msg("Verifying...")}></ak-empty-state>`;
    }

    render() {
        if (this.embedded) {
            if (!this.challenge.interactive) {
                return html``;
            }
            return this.renderBody();
        }
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
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
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-captcha": CaptchaStage;
    }
}
