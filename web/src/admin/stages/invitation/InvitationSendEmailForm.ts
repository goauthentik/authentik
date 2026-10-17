import "#elements/buttons/SpinnerButton/index";
import "#components/ak-textarea-input";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { aki } from "#common/api/client";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { showMessage } from "#elements/messages/MessageContainer";

import { type DescriptionPair, renderDescriptionList } from "#components/DescriptionList";

import { AKEmailTemplateField } from "#admin/common/AKEmailTemplateSearch";

import { Invitation, StagesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

interface InvitationSendEmailRequestWithTemplate {
    emailAddresses: string;
    ccAddresses?: string;
    bccAddresses?: string;
    template: string;
}

@customElement("ak-invitation-send-email-form")
export class InvitationSendEmailForm extends Form<InvitationSendEmailRequestWithTemplate> {
    static get styles(): CSSResult[] {
        return [...super.styles, PFDescriptionList];
    }

    @property({ attribute: false })
    invitation?: Invitation;

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
            await aki(StagesApi).stagesInvitationInvitationsSendEmailCreate({
                inviteUuid: this.invitation?.pk || "",
                invitationSendEmailRequest: {
                    emailAddresses: addresses,
                    ccAddresses: ccAddresses.length > 0 ? ccAddresses : undefined,
                    bccAddresses: bccAddresses.length > 0 ? bccAddresses : undefined,
                    template: data.template,
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

        return html`${renderDescriptionList(invitationInfo, { horizontal: true, twocolumn: true })}
            <ak-textarea-input
                label=${msg("To")}
                name="emailAddresses"
                required
                help=${msg(
                    "One email address per line, or comma/semicolon separated. Each recipient will receive a separate email with an invitation link.",
                )}
            >
            </ak-textarea-input>
            <ak-textarea-input
                label=${msg("CC")}
                name="ccAddresses"
                help=${msg(
                    "A comma-separated list of addresses to receive copies of the invitation. Recipients will receive the full list of other addresses in this list.",
                )}
            >
            </ak-textarea-input>
            <ak-textarea-input
                label=${msg("BCC")}
                name="bccAddresses"
                help=${msg(
                    "A comma-separated list of addresses to receive copies of the invitation. Recipients will not receive the addresses of other recipients.",
                )}
            >
            </ak-textarea-input>
            ${AKEmailTemplateField({
                name: "template",
                required: true,
                defaultTemplate: "goauthentik.io/email/invitation",
                help: msg("Select the email template to use for sending invitations."),
            })}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-invitation-send-email-form": InvitationSendEmailForm;
    }
}
