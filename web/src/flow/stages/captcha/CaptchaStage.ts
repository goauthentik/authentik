///<reference types="@hcaptcha/types"/>
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import { BaseStage } from "@goauthentik/flow/stages/base";
import type { TurnstileObject } from "turnstile-types";

import { msg } from "@lit/localize";
import { CSSResult, PropertyValues, TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

interface TurnstileWindow extends Window {
    turnstile: TurnstileObject;
}

const captchaContainerID = "captcha-container";

@customElement("ak-stage-captcha")
export class CaptchaStage extends BaseStage<CaptchaChallenge, CaptchaChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];
    }

    handlers = [this.handleGReCaptcha, this.handleHCaptcha, this.handleTurnstile];

    @state()
    error?: string;

    @state()
    captchaInteractive: boolean = true;

    @state()
    captchaContainer: HTMLDivElement;

    @state()
    scriptElement?: HTMLScriptElement;

    constructor() {
        super();
        this.captchaContainer = document.createElement("div");
        this.captchaContainer.id = captchaContainerID;
    }

    updated(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("challenge") && this.challenge !== undefined) {
            this.scriptElement = document.createElement("script");
            this.scriptElement.src = this.challenge.jsUrl;
            this.scriptElement.async = true;
            this.scriptElement.defer = true;
            this.scriptElement.dataset.akCaptchaScript = "true";
            this.scriptElement.onload = () => {
                console.debug("authentik/stages/captcha: script loaded");
                let found = false;
                let lastError = undefined;
                this.handlers.forEach((handler) => {
                    let handlerFound = false;
                    try {
                        console.debug(`authentik/stages/captcha[${handler.name}]: trying handler`);
                        handlerFound = handler.apply(this);
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

    handleGReCaptcha(): boolean {
        if (!Object.hasOwn(window, "grecaptcha")) {
            return false;
        }
        this.captchaInteractive = false;
        document.body.appendChild(this.captchaContainer);
        grecaptcha.ready(() => {
            const captchaId = grecaptcha.render(this.captchaContainer, {
                sitekey: this.challenge.siteKey,
                callback: (token) => {
                    this.host?.submit({
                        token: token,
                    });
                },
                size: "invisible",
            });
            grecaptcha.execute(captchaId);
        });
        return true;
    }

    handleHCaptcha(): boolean {
        if (!Object.hasOwn(window, "hcaptcha")) {
            return false;
        }
        this.captchaInteractive = false;
        document.body.appendChild(this.captchaContainer);
        const captchaId = hcaptcha.render(this.captchaContainer, {
            sitekey: this.challenge.siteKey,
            size: "invisible",
            callback: (token) => {
                this.host?.submit({
                    token: token,
                });
            },
        });
        hcaptcha.execute(captchaId);
        return true;
    }

    handleTurnstile(): boolean {
        if (!Object.hasOwn(window, "turnstile")) {
            return false;
        }
        this.captchaInteractive = false;
        document.body.appendChild(this.captchaContainer);
        (window as unknown as TurnstileWindow).turnstile.render(`#${captchaContainerID}`, {
            sitekey: this.challenge.siteKey,
            callback: (token) => {
                this.host?.submit({
                    token: token,
                });
            },
        });
        return true;
    }

    renderBody(): TemplateResult {
        if (this.error) {
            return html`<ak-empty-state icon="fa-times" header=${this.error}> </ak-empty-state>`;
        }
        if (this.captchaInteractive) {
            return html`${this.captchaContainer}`;
        }
        return html`<ak-empty-state
            ?loading=${true}
            header=${msg("Verifying...")}
        ></ak-empty-state>`;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state ?loading="${true}" header=${msg("Loading")}>
            </ak-empty-state>`;
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
