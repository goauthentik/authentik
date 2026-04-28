import "#components/ak-textarea-input";
import "#elements/forms/HorizontalFormElement";

import type { InvitationWizardState } from "./types";

import { DEFAULT_CONFIG } from "#common/api/config";
import {
    parseAPIResponseError,
    pluckErrorDetail,
    pluckFallbackFieldErrors,
} from "#common/errors/network";
import { AKRefreshEvent } from "#common/events";
import { MessageLevel } from "#common/messages";

import { showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { WizardPage } from "#elements/wizard/WizardPage";

import { StagesApi, TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-invitation-wizard-email-step")
export class InvitationWizardEmailStep extends WizardPage {
    static styles: CSSResult[] = [PFBase, PFForm, PFFormControl];

    @state()
    toAddresses = "";

    @state()
    ccAddresses = "";

    @state()
    bccAddresses = "";

    @state()
    template = "email/invitation.html";

    @state()
    availableTemplates: TypeCreate[] = [];

    override formatNextLabel(): SlottedTemplateResult {
        return html`${msg("Send")}
            <span class="pf-c-button__icon pf-m-end">
                <i class="fas fa-paper-plane" aria-hidden="true"></i>
            </span>`;
    }

    activeCallback = async (): Promise<void> => {
        this.host.valid = this.toAddresses.trim().length > 0;
        try {
            this.availableTemplates = await new StagesApi(
                DEFAULT_CONFIG,
            ).stagesEmailTemplatesList();
        } catch {
            this.availableTemplates = [];
        }
    };

    parseEmailAddresses(raw: string): string[] {
        return raw
            .split(/[\n,;]/)
            .map((value) => value.trim())
            .filter((value) => value.length > 0);
    }

    validate(): void {
        this.host.valid = this.parseEmailAddresses(this.toAddresses).length > 0;
    }

    nextCallback = async (): Promise<boolean> => {
        const wizardState = this.host.state as unknown as InvitationWizardState;
        const invitationPk = wizardState.createdInvitationPk;
        if (!invitationPk) {
            showMessage({
                level: MessageLevel.error,
                message: msg("No invitation available to send"),
            });
            return false;
        }

        const to = this.parseEmailAddresses(this.toAddresses);
        if (to.length === 0) {
            showMessage({
                level: MessageLevel.error,
                message: msg("Please enter at least one email address"),
            });
            return false;
        }
        const cc = this.parseEmailAddresses(this.ccAddresses);
        const bcc = this.parseEmailAddresses(this.bccAddresses);

        try {
            await new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsSendEmailCreate({
                inviteUuid: invitationPk,
                invitationSendEmailRequest: {
                    emailAddresses: to,
                    ccAddresses: cc.length > 0 ? cc : undefined,
                    bccAddresses: bcc.length > 0 ? bcc : undefined,
                    template: this.template,
                },
            });
        } catch (err) {
            const parsed = await parseAPIResponseError(err);
            const fieldErrors = pluckFallbackFieldErrors(parsed);
            const detail =
                fieldErrors.length > 0 ? fieldErrors.join(" ") : pluckErrorDetail(parsed);
            showMessage({
                level: MessageLevel.error,
                message: msg("Failed to queue invitation emails"),
                description: detail,
            });
            return false;
        }

        showMessage({
            level: MessageLevel.success,
            message: msg(
                str`Invitation emails queued for sending to ${to.length} recipient(s). Check the System Tasks for more information.`,
            ),
        });
        this.dispatchEvent(new AKRefreshEvent());
        return true;
    };

    override reset(): void {
        this.toAddresses = "";
        this.ccAddresses = "";
        this.bccAddresses = "";
        this.template = "email/invitation.html";
    }

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("To")} required>
                <textarea
                    class="pf-c-form-control"
                    required
                    rows="3"
                    .value=${this.toAddresses}
                    @input=${(ev: InputEvent) => {
                        this.toAddresses = (ev.target as HTMLTextAreaElement).value;
                        this.validate();
                    }}
                ></textarea>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "One email address per line, or comma/semicolon separated. Each recipient will receive a separate email with an invitation link.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("CC")}>
                <textarea
                    class="pf-c-form-control"
                    rows="2"
                    .value=${this.ccAddresses}
                    @input=${(ev: InputEvent) => {
                        this.ccAddresses = (ev.target as HTMLTextAreaElement).value;
                    }}
                ></textarea>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "A comma-separated list of addresses to receive copies of the invitation. Recipients will receive the full list of other addresses in this list.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("BCC")}>
                <textarea
                    class="pf-c-form-control"
                    rows="2"
                    .value=${this.bccAddresses}
                    @input=${(ev: InputEvent) => {
                        this.bccAddresses = (ev.target as HTMLTextAreaElement).value;
                    }}
                ></textarea>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "A comma-separated list of addresses to receive copies of the invitation. Recipients will not receive the addresses of other recipients.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Template")} required>
                <select
                    class="pf-c-form-control"
                    @change=${(ev: Event) => {
                        this.template = (ev.target as HTMLSelectElement).value;
                    }}
                >
                    ${this.availableTemplates.map(
                        (template) =>
                            html`<option
                                value=${template.name}
                                ?selected=${template.name === this.template}
                            >
                                ${template.description}
                            </option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg("Select the email template to use for sending invitations.")}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-wizard-email-step": InvitationWizardEmailStep;
    }
}
