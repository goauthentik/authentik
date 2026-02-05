import "#elements/buttons/SpinnerButton/index";
import "#components/ak-textarea-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { showMessage } from "#elements/messages/MessageContainer";
import { type DescriptionPair, renderDescriptionList } from "#components/DescriptionList";

import { Invitation, StagesApi, TypeCreate } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

interface InvitationSendEmailRequestWithTemplate {
    emailAddresses: string;
    ccAddresses?: string;
    bccAddresses?: string;
    template?: TypeCreate;
}

@customElement("ak-invitation-send-email-form")
export class InvitationSendEmailForm extends Form<InvitationSendEmailRequestWithTemplate> {
    static get styles(): CSSResult[] {
        return [...super.styles, PFDescriptionList];
    }

    @property({ attribute: false })
    invitation?: Invitation;

    @state()
    availableTemplates: TypeCreate[] = [];

    @state()
    selectedTemplate = "email/invitation.html";

    fetchAvailableTemplates = async (): Promise<void> => {
        try {
            this.availableTemplates = await new StagesApi(
                DEFAULT_CONFIG,
            ).stagesEmailTemplatesList();
        } catch (error) {
            console.error("Failed to fetch email templates:", error);
        }
    };

    connectedCallback(): void {
        super.connectedCallback();
        this.addEventListener("ak-modal-show", this.fetchAvailableTemplates);
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener("ak-modal-show", this.fetchAvailableTemplates);
    }

    parseEmailAddresses(addresses: string): string[] {
        return addresses
            .split(/[\n,;]/)
            .map((email) => email.trim())
            .filter((email) => email.length > 0);
    }

    async send(data: InvitationSendEmailRequestWithTemplate): Promise<void> {
        const addresses = this.parseEmailAddresses(data.emailAddresses);
        const ccAddresses = this.parseEmailAddresses(data.ccAddresses ?? "");
        const bccAddresses = this.parseEmailAddresses(data.bccAddresses ?? "");

        if (addresses.length === 0) {
            showMessage({
                message: msg("Please enter at least one email address"),
                level: MessageLevel.error,
            });
            return;
        }

        try {
            await new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsSendEmailCreate({
                inviteUuid: this.invitation?.pk || "",
                invitationSendEmailRequest: {
                    emailAddresses: addresses,
                    ccAddresses: ccAddresses.length > 0 ? ccAddresses : undefined,
                    bccAddresses: bccAddresses.length > 0 ? bccAddresses : undefined,
                    template: data.template?.name,
                },
            });

            showMessage({
                message: msg(
                    str`Invitation emails queued for sending to ${addresses.length} recipient(s). Check the System Tasks for more information.`,
                ),
                level: MessageLevel.success,
            });
        } catch (error) {
            showMessage({
                message: msg(str`Failed to queue invitation emails: ${error}`),
                level: MessageLevel.error,
            });
        }
    }

    protected override renderForm(): TemplateResult {
        const expiresDisplay = this.invitation?.expires
            ? this.invitation.expires.toLocaleString()
            : msg("Never");

        const invitationInfo: DescriptionPair[] = [
            [msg("Name"), this.invitation?.name ?? "-"],
            [msg("Expires"), expiresDisplay],
            [msg("Flow"), this.invitation?.flowObj?.slug ?? msg("No flow set")],
            [msg("Single use"), this.invitation?.singleUse ? msg("Yes") : msg("No")],
        ];

        return html` <ak-form-group open label="${msg("Invitation details")}">
            <div class="pf-c-card__body">
            ${renderDescriptionList(invitationInfo, { twocolumn: true })}
            </div>
            </ak-form-group>
            <ak-form-group open label="${msg("Send Email")}">
            <ak-textarea-input
                label=${msg("To")}
                name="emailAddresses"
                required
                help=${msg(
                    "One per line, or comma/semicolon separated. Each recipient will receive a separate email with an invitation link.",
                )}
            >
            </ak-textarea-input>
            <ak-textarea-input
                label=${msg("CC")}
                name="ccAddresses"
                help=${msg("Optional. Carbon copy recipients.")}
            >
            </ak-textarea-input>
            <ak-textarea-input
                label=${msg("BCC")}
                name="bccAddresses"
                help=${msg("Optional. Blind carbon copy recipients.")}
            >
            </ak-textarea-input>
            <ak-form-element-horizontal label=${msg("Template")} required name="template">
                <select class="pf-c-form-control">
                    ${this.availableTemplates?.map((template) => {
                        return html`<option
                            value=${template.name}
                            ?selected=${template.name === this.selectedTemplate}
                        >
                            ${template.description}
                        </option>`;
                    })}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg("Select the email template to use for sending invitations.")}
                </p>
            </ak-form-element-horizontal>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-send-email-form": InvitationSendEmailForm;
    }
}
