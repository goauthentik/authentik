///<reference types="@hcaptcha/types"/>
///<reference types="turnstile-types"/>
import "@goauthentik/elements/EmptyState";
import { PFSize } from "@goauthentik/elements/Spinner";
import "@goauthentik/elements/forms/FormElement";
import "@goauthentik/flow/FormStatic";
import "@goauthentik/flow/stages/access_denied/AccessDeniedStage";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CaptchaChallenge, CaptchaChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-captcha")
export class CaptchaStage extends BaseStage<CaptchaChallenge, CaptchaChallengeResponseRequest> {
    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFTitle, PFButton];
    }

    handlers = [this.handleGReCaptcha, this.handleHCaptcha, this.handleTurnstile];

    @state()
    error?: string;

    firstUpdated(): void {
        const script = document.createElement("script");
        script.src = this.challenge.jsUrl;
        script.async = true;
        script.defer = true;
        const captchaContainer = document.createElement("div");
        document.body.appendChild(captchaContainer);
        script.onload = () => {
            console.debug("authentik/stages/captcha: script loaded");
            let found = false;
            let lastError = undefined;
            this.handlers.forEach((handler) => {
                let handlerFound = false;
                try {
                    console.debug(`authentik/stages/captcha[${handler.name}]: trying handler`);
                    handlerFound = handler.apply(this, [captchaContainer]);
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
        document.head.appendChild(script);
    }

    handleGReCaptcha(container: HTMLDivElement): boolean {
        if (!Object.hasOwn(window, "grecaptcha")) {
            return false;
        }
        grecaptcha.ready(() => {
            const captchaId = grecaptcha.render(container, {
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

    handleHCaptcha(container: HTMLDivElement): boolean {
        if (!Object.hasOwn(window, "hcaptcha")) {
            return false;
        }
        const captchaId = hcaptcha.render(container, {
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

    handleTurnstile(container: HTMLDivElement): boolean {
        if (!Object.hasOwn(window, "turnstile")) {
            return false;
        }
        window.turnstile.render(container, {
            sitekey: this.challenge.siteKey,
            size: "invisible",
            callback: (token) => {
                this.host?.submit({
                    token: token,
                });
            },
        });
        return true;
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
                    ${this.error
                        ? html`<ak-stage-access-denied-icon errorMessage=${ifDefined(this.error)}>
                          </ak-stage-access-denied-icon>`
                        : html`<div>
                              <ak-spinner size=${PFSize.XLarge}></ak-spinner>
                          </div>`}
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}
