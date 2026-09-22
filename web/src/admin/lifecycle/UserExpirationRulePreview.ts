import "#elements/EmptyState";
import { aki } from "#common/api/client";

import { ModalButton } from "#elements/buttons/ModalButton";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { toAdminInterface } from "#elements/router/core/interfaces";
import { SlottedTemplateResult } from "#elements/types";

import { LifecycleApi, UserExpirationRule, UserExpirationRulePreview } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

/**
 * Show who the next run of an expiration rule would schedule an offboarding for.
 *
 * The preview reflects the rule as it is saved, not unsaved edits, so it is offered
 * from the rule list rather than from the form.
 */
@customElement("ak-user-expiration-rule-preview")
export class UserExpirationRulePreviewModal extends ModalButton {
    @property({ attribute: false })
    public rule?: UserExpirationRule;

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
            this.preview = await this.#api.lifecycleUserExpirationRulesPreviewRetrieve({
                id: this.rule.pk,
            });
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
                    >${msg("No users are due to expire under this rule right now.", {
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

        const { count } = this.preview;

        return html`<p>
                ${msg(
                    str`The next run of this rule would schedule an offboarding for ${count} user(s).`,
                    { id: "user-expiration.preview.count" },
                )}
            </p>
            ${this.renderUsers(this.preview)}
            <p>
                ${msg(
                    "Users who already have an offboarding scheduled, and users exempted by a canceled one, are not listed.",
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
