import "#elements/forms/HorizontalFormElement";

import { AccountLockdownFormBase, AccountLockdownRequest } from "./AccountLockdownFormBase";

import { EVENT_REFRESH } from "#common/constants";
import { APIMessage, MessageLevel } from "#common/messages";

import { ModalForm } from "#elements/forms/ModalForm";
import { showMessage } from "#elements/messages/MessageContainer";

import { AccountLockdownBulkResponse, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface BulkAccountLockdownRequest extends AccountLockdownRequest {
    users: number[];
}

interface SkippedUser {
    username: string;
    reason: string;
}

@customElement("ak-user-bulk-account-lockdown-form")
export class UserBulkAccountLockdownForm extends AccountLockdownFormBase<BulkAccountLockdownRequest> {
    @property({ attribute: false })
    public users: User[] = [];

    @state()
    private result?: AccountLockdownBulkResponse;

    protected override get accountCount(): number {
        return this.users.length;
    }

    /**
     * Find the parent modal and update the submit button visibility
     */
    private setSubmitButtonVisible(visible: boolean): void {
        const modal = this.closest<ModalForm>("ak-forms-modal");
        if (modal) {
            modal.showSubmitButton = visible;
        }
    }

    /**
     * Reset form state when modal is closed or form is reset
     */
    public override reset(): void {
        super.reset();
        this.result = undefined;
        this.setSubmitButtonVisible(true);
    }

    /**
     * Parse the skipped array which contains either strings or objects with username/reason
     */
    private parseSkipped(): SkippedUser[] {
        if (!this.result?.skipped) return [];
        return this.result.skipped.map((item) => {
            if (typeof item === "string") {
                return { username: item, reason: msg("Unknown reason") };
            }
            // The API returns objects with username and reason
            const obj = item as unknown as SkippedUser;
            return { username: obj.username, reason: obj.reason };
        });
    }

    protected override formatAPISuccessMessage(response: unknown): APIMessage | null {
        const result = response as AccountLockdownBulkResponse;
        const processedCount = result.processed?.length ?? 0;
        const skippedCount = result.skipped?.length ?? 0;

        // If there were skipped users, show a warning instead of success
        if (skippedCount > 0) {
            const lockedMsg =
                processedCount === 1
                    ? msg("Locked 1 account")
                    : msg(str`Locked ${processedCount} accounts`);
            const skippedMsg =
                skippedCount === 1 ? msg("1 was skipped") : msg(str`${skippedCount} were skipped`);
            const failedMsg =
                skippedCount === 1
                    ? msg("Failed to lock 1 account.")
                    : msg(str`Failed to lock ${skippedCount} accounts.`);

            return {
                level: processedCount > 0 ? MessageLevel.warning : MessageLevel.error,
                message:
                    processedCount > 0 ? msg(str`${lockedMsg}, but ${skippedMsg}.`) : failedMsg,
            };
        }

        return {
            level: MessageLevel.success,
            message:
                processedCount === 1
                    ? msg("Account lockdown triggered for 1 user.")
                    : msg(str`Account lockdown triggered for ${processedCount} users.`),
            description: msg("The accounts have been secured."),
        };
    }

    async send(data: BulkAccountLockdownRequest): Promise<AccountLockdownBulkResponse> {
        const response = await this.coreApi.coreUsersAccountLockdownBulkCreate({
            userBulkAccountLockdownRequest: {
                ...data,
                users: this.users.map((u) => u.pk),
            },
        });

        // Store result for display
        this.result = response;

        // Hide the submit button since we're showing results
        this.setSubmitButtonVisible(false);

        // Dispatch refresh event to update user list
        this.dispatchEvent(
            new CustomEvent(EVENT_REFRESH, {
                bubbles: true,
                composed: true,
            }),
        );

        // If there were skipped users, throw to prevent modal from closing
        if (response.skipped && response.skipped.length > 0) {
            // Show the success message manually since we're going to throw
            showMessage(this.formatAPISuccessMessage(response));
            // Throw a special error that won't show an error message
            const error = new Error("Some users were skipped");
            (error as Error & { silent?: boolean }).silent = true;
            throw error;
        }

        return response;
    }

    protected renderAffectedUsers(): TemplateResult {
        const count = this.users.length;
        const label = count === 1 ? msg("Affected user (1)") : msg(str`Affected users (${count})`);

        return html`
            <ak-form-element-horizontal label=${label}>
                <div class="user-list">
                    <ul class="pf-c-list">
                        ${this.users.map(
                            (user) => html`
                                <li>
                                    <strong>${user.username}</strong>
                                    ${user.name ? html` - ${user.name}` : html``}
                                </li>
                            `,
                        )}
                    </ul>
                </div>
            </ak-form-element-horizontal>
        `;
    }

    protected renderResults(): TemplateResult {
        if (!this.result) return html`${nothing}`;

        const processed = this.result.processed ?? [];
        const skipped = this.parseSkipped();

        const successTitle =
            processed.length === 1
                ? msg("Successfully locked 1 account")
                : msg(str`Successfully locked ${processed.length} accounts`);

        const skippedTitle =
            skipped.length === 1
                ? msg("1 account was skipped")
                : msg(str`${skipped.length} accounts were skipped`);

        return html`
            ${processed.length > 0
                ? html`
                      <div class="pf-c-alert pf-m-success pf-m-inline">
                          <div class="pf-c-alert__icon">
                              <i class="fas fa-fw fa-check-circle" aria-hidden="true"></i>
                          </div>
                          <h4 class="pf-c-alert__title">${successTitle}</h4>
                          <div class="pf-c-alert__description">
                              <ul class="pf-c-list">
                                  ${processed.map((username) => html`<li>${username}</li>`)}
                              </ul>
                          </div>
                      </div>
                  `
                : nothing}
            ${skipped.length > 0
                ? html`
                      <div class="pf-c-alert pf-m-warning pf-m-inline">
                          <div class="pf-c-alert__icon">
                              <i class="fas fa-fw fa-exclamation-triangle" aria-hidden="true"></i>
                          </div>
                          <h4 class="pf-c-alert__title">${skippedTitle}</h4>
                          <div class="pf-c-alert__description">
                              <ul class="pf-c-list">
                                  ${skipped.map(
                                      (item) =>
                                          html`<li>
                                              <strong>${item.username}</strong>: ${item.reason}
                                          </li>`,
                                  )}
                              </ul>
                          </div>
                      </div>
                  `
                : nothing}
        `;
    }

    override renderForm(): TemplateResult {
        // If we have results, show them instead of the form
        if (this.result) {
            return this.renderResults();
        }

        return html`
            ${this.renderWarningAlert()} ${this.renderInfoAlert()} ${this.renderAffectedUsers()}
            ${this.renderReasonInput()}
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-bulk-account-lockdown-form": UserBulkAccountLockdownForm;
    }
}
