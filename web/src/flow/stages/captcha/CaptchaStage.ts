///<reference types="@hcaptcha/types"/>
import { renderStatic } from "@goauthentik/common/purify";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import { randomId } from "@goauthentik/elements/utils/randomId";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

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
                }
            `,
        ];
    }

    handlers = [this.handleGReCaptcha, this.handleHCaptcha, this.handleTurnstile];

    @state()
    error?: string;

    @state()
    captchaInteractive: boolean = true;

    @state()
    captchaContainer: HTMLIFrameElement;

    @state()
    scriptElement?: HTMLScriptElement;

    @property()
    onTokenChange: TokenHandler = (token: string) => {
        this.host.submit({ component: "ak-stage-captcha", token });
    };

    constructor() {
        super();
        this.captchaContainer = document.createElement("iframe");
        this.captchaContainer.src = "about:blank";
        this.captchaContainer.id = `ak-captcha-${randomId()}`;
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
        }
    }

    async handleGReCaptcha(): Promise<boolean> {
        if (!Object.hasOwn(window, "grecaptcha")) {
            return false;
        }
        this.captchaInteractive = false;
        document.body.appendChild(this.captchaContainer);
        grecaptcha.ready(() => {
            const captchaId = grecaptcha.render(this.captchaContainer, {
                sitekey: this.challenge.siteKey,
                callback: this.onTokenChange,
                size: "invisible",
            });
            grecaptcha.execute(captchaId);
        });
        return true;
    }

    async handleHCaptcha(): Promise<boolean> {
        if (!Object.hasOwn(window, "hcaptcha")) {
            return false;
        }
        this.captchaInteractive = false;
        document.body.appendChild(this.captchaContainer);
        const captchaId = hcaptcha.render(this.captchaContainer, {
            sitekey: this.challenge.siteKey,
            callback: this.onTokenChange,
            size: "invisible",
        });
        hcaptcha.execute(captchaId);
        return true;
    }

    async handleTurnstile(): Promise<boolean> {
        if (!Object.hasOwn(window, "turnstile")) {
            return false;
        }
        this.captchaInteractive = true;
        window.addEventListener("message", (event) => {
            const msg: {
                source?: string;
                context?: string;
                message: string;
                token: string;
            } = event.data;
            if (msg.source !== "goauthentik.io" || msg.context !== "flow-executor") {
                return;
            }
            if (msg.message !== "captcha") {
                return;
            }
            this.onTokenChange(msg.token);
        });
        this.captchaContainer.contentWindow?.document.open();
        this.captchaContainer.contentWindow?.document.write(
            await renderStatic(
                html`<!doctype html>
                    <html>
                        <body style="display:flex;flex-direction:row;justify-content:center;">
                            <div
                                class="cf-turnstile"
                                data-sitekey="${this.challenge.siteKey}"
                                data-callback="callback"
                            ></div>
                            <script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script>
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
        this.captchaContainer.contentWindow?.document.close();
        return true;
    }

    renderBody() {
        if (this.error) {
            return html`<ak-empty-state icon="fa-times" header=${this.error}> </ak-empty-state>`;
        }
        if (this.captchaInteractive) {
            return html`${this.captchaContainer}`;
        }
        return html`<ak-empty-state loading header=${msg("Verifying...")}></ak-empty-state>`;
    }

    render() {
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
