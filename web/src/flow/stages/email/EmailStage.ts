import "@goauthentik/elements/EmptyState";
import { BaseStage } from "@goauthentik/flow/stages/base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EmailChallenge, EmailChallengeResponseRequest } from "@goauthentik/api";

@customElement("ak-stage-email")
export class EmailStage extends BaseStage<EmailChallenge, EmailChallengeResponseRequest> {
    @state()
    private isLoading = false;

    @state()
    private cooldownTimer = 0;

    @state()
    private attempts = 0;

    private cooldownInterval?: number;
    private readonly COOLDOWN_DURATION = 60; // 60 seconds
    private readonly MAX_ATTEMPTS = 5; // Maximum attempts before longer cooldown
    private readonly EXTENDED_COOLDOWN = 300; // 5 minutes for excessive attempts

    static get styles(): CSSResult[] {
        return [PFBase, PFLogin, PFForm, PFFormControl, PFButton, PFTitle];
    }

    connectedCallback() {
        super.connectedCallback();
        // Check if there's a stored cooldown state
        this.restoreCooldownState();
    }

    disconnectedCallback() {
        super.disconnectedCallback();
        if (this.cooldownInterval) {
            clearInterval(this.cooldownInterval);
        }
    }

    private restoreCooldownState() {
        const lastAttempt = sessionStorage.getItem('ak-email-stage-last-attempt');
        const storedAttempts = sessionStorage.getItem('ak-email-stage-attempts');
        
        if (lastAttempt && storedAttempts) {
            const timeSinceLastAttempt = Date.now() - parseInt(lastAttempt, 10);
            this.attempts = parseInt(storedAttempts, 10);
            
            const cooldownDuration = this.attempts >= this.MAX_ATTEMPTS ? 
                this.EXTENDED_COOLDOWN : this.COOLDOWN_DURATION;
            
            if (timeSinceLastAttempt < cooldownDuration * 1000) {
                this.cooldownTimer = Math.ceil((cooldownDuration * 1000 - timeSinceLastAttempt) / 1000);
                this.startCooldownTimer();
            } else {
                // Cooldown expired, reset attempts if enough time has passed
                if (timeSinceLastAttempt > this.EXTENDED_COOLDOWN * 1000) {
                    this.attempts = 0;
                    sessionStorage.removeItem('ak-email-stage-attempts');
                    sessionStorage.removeItem('ak-email-stage-last-attempt');
                }
            }
        }
    }

    private startCooldownTimer() {
        if (this.cooldownInterval) {
            clearInterval(this.cooldownInterval);
        }
        
        this.cooldownInterval = setInterval(() => {
            this.cooldownTimer--;
            if (this.cooldownTimer <= 0) {
                clearInterval(this.cooldownInterval);
                this.cooldownInterval = undefined;
            }
        }, 1000);
    }

    private trackAttempt() {
        this.attempts++;
        const now = Date.now();
        sessionStorage.setItem('ak-email-stage-last-attempt', now.toString());
        sessionStorage.setItem('ak-email-stage-attempts', this.attempts.toString());
        
        const cooldownDuration = this.attempts >= this.MAX_ATTEMPTS ? 
            this.EXTENDED_COOLDOWN : this.COOLDOWN_DURATION;
        
        this.cooldownTimer = cooldownDuration;
        this.startCooldownTimer();
    }

    async submitForm(e: Event, defaults?: EmailChallengeResponseRequest): Promise<boolean> {
        e.preventDefault();
        
        if (this.isLoading || this.cooldownTimer > 0) {
            return false;
        }

        this.isLoading = true;
        this.trackAttempt();

        try {
            const result = await super.submitForm(e, defaults);
            return result;
        } catch (error) {
            // Handle any errors
            console.error('Email send failed:', error);
            return false;
        } finally {
            this.isLoading = false;
        }
    }

    onSubmitSuccess(): void {
        // Reset attempts on successful submission
        this.attempts = 0;
        sessionStorage.removeItem('ak-email-stage-attempts');
        sessionStorage.removeItem('ak-email-stage-last-attempt');
        super.onSubmitSuccess();
    }

    private getButtonText(): string {
        if (this.isLoading) {
            return msg("Sending...");
        }
        if (this.cooldownTimer > 0) {
            const minutes = Math.floor(this.cooldownTimer / 60);
            const seconds = this.cooldownTimer % 60;
            if (minutes > 0) {
                return msg(`Wait ${minutes}m ${seconds}s`);
            }
            return msg(`Wait ${seconds}s`);
        }
        return msg("Send Email again.");
    }

    private getButtonDisabled(): boolean {
        return this.isLoading || this.cooldownTimer > 0;
    }

    private renderWarningMessage(): TemplateResult | typeof html.nothing {
        if (this.attempts >= this.MAX_ATTEMPTS) {
            return html`<div class="pf-c-form__group">
                <div class="pf-c-alert pf-m-inline pf-m-warning">
                    <div class="pf-c-alert__icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h4 class="pf-c-alert__title">
                        ${msg("Too many attempts. Extended cooldown in effect.")}
                    </h4>
                </div>
            </div>`;
        } else if (this.attempts >= 3) {
            return html`<div class="pf-c-form__group">
                <div class="pf-c-alert pf-m-inline pf-m-info">
                    <div class="pf-c-alert__icon">
                        <i class="fas fa-info-circle"></i>
                    </div>
                    <h4 class="pf-c-alert__title">
                        ${msg("Please check your spam folder if you haven't received the email.")}
                    </h4>
                </div>
            </div>`;
        }
        return html.nothing;
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-empty-state loading> </ak-empty-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">${this.challenge.flowInfo?.title}</h1>
            </header>
            <div class="pf-c-login__main-body">
                <form
                    class="pf-c-form"
                    @submit=${(e: Event) => {
                        this.submitForm(e);
                    }}
                >
                    <div class="pf-c-form__group">
                        <span class="email-icon">📧</span>
                        <p>${msg("Check your Inbox for a verification email.")}</p>
                    </div>

                    ${this.renderWarningMessage()}

                    <div class="pf-c-form__group pf-m-action">
                        <button 
                            type="submit" 
                            class="pf-c-button pf-m-primary pf-m-block"
                            ?disabled=${this.getButtonDisabled()}
                            aria-label=${this.getButtonText()}
                        >
                            ${this.getButtonText()}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links"></ul>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-email": EmailStage;
    }
}
