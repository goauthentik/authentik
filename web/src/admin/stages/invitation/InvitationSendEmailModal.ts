import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH } from "#common/constants";
import { MessageLevel } from "#common/messages";

import { ModalButton } from "#elements/buttons/ModalButton";
import { showMessage } from "#elements/messages/MessageContainer";

import { Invitation, StagesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

@customElement("ak-invitation-send-email-modal")
export class InvitationSendEmailModal extends ModalButton {
    @property({ attribute: false })
    invitation?: Invitation;

    @state()
    emailAddresses: string = "";

    @state()
    isSending = false;

    static styles: CSSResult[] = [PFForm, PFFormControl];

    parseEmailAddresses(): string[] {
        return this.emailAddresses
            .split(/[\n,;]/)
            .map((email) => email.trim())
            .filter((email) => email.length > 0);
    }

    async sendEmails(): Promise<void> {
        const addresses = this.parseEmailAddresses();

        if (addresses.length === 0) {
            showMessage({
                message: msg("Please enter at least one email address"),
                level: MessageLevel.error,
            });
            return;
        }

        this.isSending = true;

        try {
            const response = await new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsSendEmailCreate(
                {
                    inviteUuid: this.invitation?.pk || "",
                    invitationSendEmailRequest: {
                        emailAddresses: addresses,
                    },
                },
            );

            if (response.failedCount > 0) {
                showMessage({
                    message: msg(
                        str`Sent invitations to ${response.sentCount} address(es), failed for ${response.failedCount} address(es)`,
                    ),
                    level: MessageLevel.warning,
                });
            } else {
                showMessage({
                    message: msg(
                        str`Successfully sent invitations to ${response.sentCount} address(es)`,
                    ),
                    level: MessageLevel.success,
                });
            }

            this.dispatchEvent(
                new CustomEvent(EVENT_REFRESH, {
                    bubbles: true,
                    composed: true,
                }),
            );
            this.open = false;
            this.emailAddresses = "";
        } catch (error) {
            showMessage({
                message: msg(str`Failed to send invitations: ${error}`),
                level: MessageLevel.error,
            });
        } finally {
            this.isSending = false;
        }
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${msg("Send Invitation via Email")}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">
                <form class="pf-c-form pf-m-horizontal">
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="email-addresses">
                            <span class="pf-c-form__label-text"
                                >${msg("Email Addresses")}</span
                            >
                            <span class="pf-c-form__label-required" aria-hidden="true">*</span>
                        </label>
                        <div class="pf-c-form__horizontal-group">
                            <textarea
                                id="email-addresses"
                                class="pf-c-form-control"
                                rows="6"
                                placeholder=${msg(
                                    "Enter email addresses (one per line, or comma/semicolon separated)",
                                )}
                                .value=${this.emailAddresses}
                                @input=${(e: Event) => {
                                    this.emailAddresses = (e.target as HTMLTextAreaElement).value;
                                }}
                            ></textarea>
                        </div>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Enter one or more email addresses. Each recipient will receive an invitation link.",
                            )}
                        </p>
                    </div>
                </form>
            </section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => this.sendEmails()}
                    class="pf-m-primary"
                    ?disabled=${this.isSending}
                >
                    ${msg("Send Invitation")}
                </ak-spinner-button>
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                        this.emailAddresses = "";
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-send-email-modal": InvitationSendEmailModal;
    }
}
