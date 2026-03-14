import "#components/ak-textarea-input";
import "#elements/Alert";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIMessage, MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";

import { CoreApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, html, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFList from "@patternfly/patternfly/components/List/list.css";

/**
 * Base request interface for account lockdown operations
 */
export interface AccountLockdownRequest {
    reason: string;
}

/**
 * Abstract base class for account lockdown forms.
 */
export abstract class AccountLockdownFormBase<T extends AccountLockdownRequest> extends Form<T> {
    /**
     * Number of accounts affected by this lockdown action.
     * Used for pluralization in warning messages.
     */
    protected get accountCount(): number {
        return 1;
    }

    static get styles() {
        return [
            ...Form.styles,
            PFAlert,
            PFList,
            css`
                ak-alert,
                .pf-c-alert {
                    margin-bottom: var(--pf-global--spacer--md);
                }

                .pf-c-alert__description ul.pf-c-list {
                    margin-top: var(--pf-global--spacer--sm);
                }

                .user-list {
                    max-height: 150px;
                    overflow-y: auto;
                    background: var(--pf-global--BackgroundColor--light-200);
                    padding: var(--pf-global--spacer--sm);
                    border-radius: var(--pf-global--BorderRadius--sm);
                    margin-top: var(--pf-global--spacer--sm);
                }
            `,
        ];
    }

    protected get coreApi(): CoreApi {
        return new CoreApi(DEFAULT_CONFIG);
    }

    /**
     * Returns the warning alert title.
     */
    protected get warningTitle(): string {
        return this.accountCount === 1
            ? msg("You are about to lock 1 account")
            : msg(str`You are about to lock ${this.accountCount} accounts`);
    }

    /**
     * Returns the info message about when to use lockdown.
     */
    protected get infoMessage(): string {
        return this.accountCount === 1
            ? msg("Use this when you suspect an account has been compromised.")
            : msg("Use this when you suspect multiple accounts have been compromised.");
    }

    /**
     * Returns the placeholder text for the reason field.
     */
    protected get reasonPlaceholder(): string {
        return this.accountCount === 1
            ? msg("Describe why this account is being locked down...")
            : msg("Describe why these accounts are being locked down...");
    }

    /**
     * Returns the help text for the reason field.
     */
    protected get reasonHelp(): string {
        return this.accountCount === 1
            ? msg("Required. This explanation will be recorded in the audit log.")
            : msg(
                  "Required. This explanation will be recorded in the audit log for each user.",
              );
    }

    /**
     * Renders the danger warning alert with the list of actions.
     */
    protected renderWarningAlert(): TemplateResult {
        return html`
            <div class="pf-c-alert pf-m-danger pf-m-inline">
                <div class="pf-c-alert__icon">
                    <i class="fas fa-fw fa-exclamation-triangle" aria-hidden="true"></i>
                </div>
                <h4 class="pf-c-alert__title">${this.warningTitle}</h4>
                <div class="pf-c-alert__description">
                    <p>${msg("This action will immediately:")}</p>
                    <ul class="pf-c-list">
                        <li>
                            ${msg("Invalidate the user's password")}
                            <ul class="pf-c-list">
                                <li>
                                    ${msg(
                                        "The password will be set to a random value and cannot be recovered",
                                    )}
                                </li>
                            </ul>
                        </li>
                        <li>
                            ${msg("Deactivate the user account")}
                            <ul class="pf-c-list">
                                <li>${msg("Terminate all active authentik sessions")}</li>
                                <li>${msg("Revoke all API tokens and OAuth tokens")}</li>
                            </ul>
                        </li>
                    </ul>
                </div>
            </div>
        `;
    }

    /**
     * Renders the info alert with documentation link.
     */
    protected renderInfoAlert(): TemplateResult {
        return html`
            <ak-alert level="info" inline>
                ${this.infoMessage}
                <a
                    href="https://docs.goauthentik.io/docs/security/account-lockdown"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    ${msg("Learn more")}
                </a>
            </ak-alert>
        `;
    }

    /**
     * Renders the affected user(s) section.
     * Override in subclasses to show single user or list of users.
     */
    protected abstract renderAffectedUsers(): TemplateResult;

    /**
     * Renders the reason textarea input.
     */
    protected renderReasonInput(): TemplateResult {
        return html`
            <ak-textarea-input
                name="reason"
                label=${msg("Reason")}
                .rows=${3}
                placeholder=${this.reasonPlaceholder}
                help=${this.reasonHelp}
                required
            ></ak-textarea-input>
        `;
    }

    renderForm(): TemplateResult {
        return html`
            ${this.renderWarningAlert()} ${this.renderInfoAlert()} ${this.renderAffectedUsers()}
            ${this.renderReasonInput()}
        `;
    }
}

/**
 * Base class for single-user account lockdown forms (admin and self-service).
 * Provides shared functionality for forms that lock a single user account.
 */
export abstract class SingleUserAccountLockdownForm extends AccountLockdownFormBase<AccountLockdownRequest> {
    @property({ type: String })
    public username?: string;

    /**
     * Success message description shown after lockdown.
     * Override in subclasses for context-specific messaging.
     */
    protected get successDescription(): string {
        return msg("The user's account has been secured.");
    }

    protected override formatAPISuccessMessage(): APIMessage | null {
        return {
            level: MessageLevel.success,
            message: msg(str`Account lockdown triggered successfully.`),
            description: this.successDescription,
        };
    }

    protected renderAffectedUsers(): TemplateResult {
        if (!this.username) {
            return html`${nothing}`;
        }
        return html`
            <ak-form-element-horizontal label=${this.affectedUserLabel}>
                <div class="pf-c-form-control-static">${this.usernameDisplay}</div>
            </ak-form-element-horizontal>
        `;
    }

    /**
     * Label for the affected user field.
     */
    protected get affectedUserLabel(): string {
        return msg("Affected user");
    }

    /**
     * How to display the username in the form.
     */
    protected get usernameDisplay(): string | TemplateResult {
        return this.username ?? "";
    }
}
