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
    ccAddresses: string = "";

    @state()
    bccAddresses: string = "";

    @state()
    isSending = false;

    static styles: CSSResult[] = [PFForm, PFFormControl];

    parseEmailAddresses(addresses: string): string[] {
        return addresses
            .split(/[\n,;]/)
            .map((email) => email.trim())
            .filter((email) => email.length > 0);
    }

    async sendEmails(): Promise<void> {
        const addresses = this.parseEmailAddresses(this.emailAddresses);
        const ccAddresses = this.parseEmailAddresses(this.ccAddresses);
        const bccAddresses = this.parseEmailAddresses(this.bccAddresses);

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
                        ccAddresses: ccAddresses.length > 0 ? ccAddresses : undefined,
                        bccAddresses: bccAddresses.length > 0 ? bccAddresses : undefined,
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
            this.ccAddresses = "";
            this.bccAddresses = "";
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
                            <span class="pf-c-form__label-text">${msg("To")}</span>
                            <span class="pf-c-form__label-required" aria-hidden="true">*</span>
                        </label>
                        <div class="pf-c-form__horizontal-group">
                            <textarea
                                id="email-addresses"
                                class="pf-c-form-control"
                                rows="2"
                                placeholder=${msg("user@example.com")}
                                .value=${this.emailAddresses}
                                @input=${(e: Event) => {
                                    this.emailAddresses = (e.target as HTMLTextAreaElement).value;
                                }}
                            ></textarea>
                            <p class="pf-c-form__helper-text">
                            ${msg(
                                "One per line, or comma/semicolon separated. Each recipient will receive an invitation link.",
                            )}
                        </p>
                        </div>

                    </div>
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="cc-addresses">
                            <span class="pf-c-form__label-text">${msg("CC")}</span>
                        </label>
                        <div class="pf-c-form__horizontal-group">
                            <textarea
                                id="cc-addresses"
                                class="pf-c-form-control"
                                rows="2"
                                placeholder=${msg("user@example.com")}
                                .value=${this.ccAddresses}
                                @input=${(e: Event) => {
                                    this.ccAddresses = (e.target as HTMLTextAreaElement).value;
                                }}
                            ></textarea>
                            <p class="pf-c-form__helper-text">
                            ${msg("Optional. Carbon copy recipients.")}
                        </p>
                        </div>
                    </div>
                    <div class="pf-c-form__group">
                        <label class="pf-c-form__label" for="bcc-addresses">
                            <span class="pf-c-form__label-text">${msg("BCC")}</span>
                        </label>
                        <div class="pf-c-form__horizontal-group">
                            <textarea
                                id="bcc-addresses"
                                class="pf-c-form-control"
                                rows="2"
                                placeholder=${msg("user@example.com")}
                                .value=${this.bccAddresses}
                                @input=${(e: Event) => {
                                    this.bccAddresses = (e.target as HTMLTextAreaElement).value;
                                }}
                            ></textarea>
                            <p class="pf-c-form__helper-text">
                            ${msg("Optional. Blind carbon copy recipients.")}
                        </p>
                        </div>

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
                        this.ccAddresses = "";
                        this.bccAddresses = "";
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
