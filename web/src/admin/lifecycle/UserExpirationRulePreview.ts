import "#elements/EmptyState";
import "#elements/timestamp/ak-timestamp";
import { aki } from "#common/api/client";

import { ModalButton } from "#elements/buttons/ModalButton";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { toAdminInterface } from "#elements/router/core/interfaces";
import { SlottedTemplateResult } from "#elements/types";

import { offboardingActionLabel } from "#admin/lifecycle/utils";

import {
    LifecycleApi,
    OffboardingActionEnum,
    UserExpirationRule,
    UserExpirationRulePendingPreviewGroup,
    UserExpirationRulePreview,
    UserExpirationRuleRequest,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

/**
 * Preview new offboardings and changes to pending rows, without saving anything.
 * The list previews the saved rule; the form supplies unsaved edits through getRequest.
 */
@customElement("ak-user-expiration-rule-preview")
export class UserExpirationRulePreviewModal extends ModalButton {
    @property({ attribute: false })
    public rule?: UserExpirationRule;

    @property({ attribute: false })
    public getRequest?: () => UserExpirationRuleRequest;

    @state()
    protected preview: UserExpirationRulePreview | null = null;

    @state()
    protected loading = false;

    #api = aki(LifecycleApi);

    public override connectedCallback(): void {
        super.connectedCallback();

        this.addEventListener("ak-modal-show", this.#fetchPreview);
    }

    public override disconnectedCallback(): void {
        this.removeEventListener("ak-modal-show", this.#fetchPreview);

        super.disconnectedCallback();
    }

    #fetchPreview = async (): Promise<void> => {
        if (!this.rule?.pk) {
            return;
        }

        this.loading = true;
        this.preview = null;

        try {
            this.preview = this.getRequest
                ? await this.#api.lifecycleUserExpirationRulesPreviewCreate({
                      id: this.rule.pk,
                      userExpirationRuleRequest: this.getRequest(),
                  })
                : await this.#api.lifecycleUserExpirationRulesPreviewRetrieve({ id: this.rule.pk });
        } catch (error) {
            showAPIErrorMessage(error);
        } finally {
            this.loading = false;
        }
    };

    protected renderUsers(preview: UserExpirationRulePreview): SlottedTemplateResult {
        if (preview.count === 0) {
            return html`<ak-empty-state icon="fa-user-check">
                <span
                    >${msg("No additional users would be scheduled.", {
                        id: "user-expiration.preview.empty",
                    })}</span
                >
            </ak-empty-state>`;
        }

        const hidden = preview.count - preview.users.length;

        // The modal body carries `pf-c-content`, which styles a plain list.
        return html`<ul>
                ${preview.users.map(
                    (user) =>
                        html`<li>
                            <a href=${toAdminInterface(`identity/users/${user.pk}`)}
                                >${user.username}</a
                            >
                            ${user.name ? html`<span> &mdash; ${user.name}</span>` : nothing}
                        </li>`,
                )}
            </ul>
            ${
                hidden > 0
                    ? html`<p>
                          ${msg(str`and ${hidden} more`, { id: "user-expiration.preview.more" })}
                      </p>`
                    : nothing
            }`;
    }

    protected renderSettings(
        action: OffboardingActionEnum | null,
        scheduledAt: Date | null,
        revokeSessions: boolean | null,
        revokeTokens: boolean | null,
    ): SlottedTemplateResult {
        if (action === null || scheduledAt === null) {
            return html`${msg("Removed", { id: "user-expiration.preview.removed.label" })}`;
        }

        return html`${offboardingActionLabel(action)}
            <ak-timestamp .timestamp=${scheduledAt} datetime></ak-timestamp>
            <span>
                ${
                    revokeSessions
                        ? msg("Revoke sessions", { id: "user-expiration.preview.sessions.revoke" })
                        : msg("Keep sessions", { id: "user-expiration.preview.sessions.keep" })
                };
                ${
                    revokeTokens
                        ? msg("Revoke tokens", { id: "user-expiration.preview.tokens.revoke" })
                        : msg("Keep tokens", { id: "user-expiration.preview.tokens.keep" })
                }
            </span>`;
    }

    protected renderPending(
        title: string,
        group: UserExpirationRulePendingPreviewGroup,
    ): SlottedTemplateResult {
        if (!group.count) {
            return nothing;
        }

        const hidden = group.count - group.offboardings.length;

        return html`<h2>${title} (${group.count})</h2>
            <ul>
                ${group.offboardings.map(
                    (row) => html`<li>
                        <a href=${toAdminInterface(`identity/users/${row.user.pk}`)}
                            >${row.user.username}</a
                        >
                        <p>
                            <strong>
                                ${msg("Before:", { id: "user-expiration.preview.before.label" })}
                            </strong>
                            ${this.renderSettings(
                                row.previousAction,
                                row.previousScheduledAt,
                                row.previousRevokeSessions,
                                row.previousRevokeTokens,
                            )}
                        </p>
                        <p>
                            <strong>
                                ${msg("After:", { id: "user-expiration.preview.after.label" })}
                            </strong>
                            ${this.renderSettings(
                                row.action,
                                row.scheduledAt,
                                row.revokeSessions,
                                row.revokeTokens,
                            )}
                        </p>
                    </li>`,
                )}
            </ul>
            ${
                hidden > 0
                    ? html`<p>
                          ${msg(str`and ${hidden} more`, { id: "user-expiration.preview.more" })}
                      </p>`
                    : nothing
            }`;
    }

    protected renderBody(): SlottedTemplateResult {
        if (this.loading) {
            return html`<ak-empty-state default-label loading></ak-empty-state>`;
        }

        if (!this.preview) {
            return html`<ak-empty-state icon="fa-times">
                <span
                    >${msg("The preview could not be loaded.", {
                        id: "user-expiration.preview.error",
                    })}</span
                >
            </ak-empty-state>`;
        }

        const { count, updated, takenOver, removed } = this.preview;

        return html`<p>
                ${
                    this.getRequest
                        ? msg("This previews your unsaved changes as if the rule were enabled.", {
                              id: "user-expiration.preview.unsaved.description",
                          })
                        : msg("This previews the saved rule as if it were enabled.", {
                              id: "user-expiration.preview.saved.description",
                          })
                }
                ${msg("Preview does not save changes or send warnings.", {
                    id: "user-expiration.preview.read-only.description",
                })}
            </p>
            <h2>${msg("New offboardings", { id: "user-expiration.preview.new.title" })}</h2>
            <p>
                ${msg(
                    str`The next run of this rule would schedule an offboarding for ${count} user(s).`,
                    { id: "user-expiration.preview.count" },
                )}
            </p>
            ${this.renderUsers(this.preview)}
            <p>
                ${msg(
                    str`Existing offboardings: ${updated.count} updated, ${takenOver.count} taken over from other rules, ${removed.count} removed.`,
                    { id: "user-expiration.preview.pending.count" },
                )}
            </p>
            ${this.renderPending(
                msg("Pending offboardings updated", {
                    id: "user-expiration.preview.updated.title",
                }),
                updated,
            )}
            ${this.renderPending(
                msg("Pending offboardings taken over from other rules", {
                    id: "user-expiration.preview.taken-over.title",
                }),
                takenOver,
            )}
            ${this.renderPending(
                msg("Pending offboardings removed", {
                    id: "user-expiration.preview.removed.title",
                }),
                removed,
            )}
            <p>
                ${msg(
                    "Manual offboardings and exemptions from canceled offboardings are not changed. Existing offboardings with unchanged settings are not listed.",
                    { id: "user-expiration.preview.exclusions" },
                )}
            </p>`;
    }

    protected override renderModalInner(): SlottedTemplateResult {
        return html`<div class="pf-c-modal-box__header">
                <h1 class="pf-c-title pf-m-2xl" id="modal-title">
                    ${msg("Expiration preview", { id: "user-expiration.preview.header" })}
                </h1>
                ${
                    this.rule
                        ? html`<p class="pf-c-modal-box__description" id="modal-description">
                              ${this.rule.name}
                          </p>`
                        : nothing
                }
            </div>
            <div class="pf-c-modal-box__body pf-c-content">${this.renderBody()}</div>
            <fieldset class="ak-c-fieldset pf-c-modal-box__footer">
                <legend class="sr-only">
                    ${msg("Form actions", { id: "common.form.actions" })}
                </legend>
                <button class="pf-c-button pf-m-primary" type="button" @click=${this.close}>
                    ${msg("Close", { id: "common.actions.close" })}
                </button>
            </fieldset>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-expiration-rule-preview": UserExpirationRulePreviewModal;
    }
}
