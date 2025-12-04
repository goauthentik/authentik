import "#components/ak-switch-input";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { APIMessage } from "#elements/messages/Message";

import { AdminApi, CoreApi, User, UserBulkPanicButtonRequest } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-user-bulk-panic-button-form")
export class UserBulkPanicButtonForm extends Form<UserBulkPanicButtonRequest> {
    @property({ attribute: false })
    public users: User[] = [];

    @state()
    private defaultNotifyUser = true;

    @state()
    private defaultNotifyAdmins = true;

    @state()
    private defaultNotifySecurity = false;

    async firstUpdated(): Promise<void> {
        try {
            const settings = await new AdminApi(DEFAULT_CONFIG).adminSettingsRetrieve();
            this.defaultNotifyUser = settings.panicButtonNotifyUser ?? true;
            this.defaultNotifyAdmins = settings.panicButtonNotifyAdmins ?? true;
            this.defaultNotifySecurity = settings.panicButtonNotifySecurity ?? false;
        } catch (error) {
            console.error("Failed to fetch panic button settings:", error);
        }
    }

    protected override formatAPISuccessMessage(): APIMessage | null {
        return {
            level: MessageLevel.success,
            message: msg(str`Panic button triggered for ${this.users.length} user(s).`),
            description: msg("The users' accounts have been secured."),
        };
    }

    async send(data: UserBulkPanicButtonRequest): Promise<void> {
        await new CoreApi(DEFAULT_CONFIG).coreUsersPanicButtonBulkCreate({
            userBulkPanicButtonRequest: {
                ...data,
                users: this.users.map((u) => u.pk),
            },
        });
    }

    renderForm(): TemplateResult {
        return html`
            <p class="pf-c-form__helper-text" style="margin-bottom: 1rem; color: #c9190b;">
                ${msg(
                    str`This action will lock ${this.users.length} account(s), reset their passwords, and terminate all their active sessions.`,
                )}
            </p>
            <p class="pf-c-form__helper-text" style="margin-bottom: 1rem;">
                <strong>${msg("Affected users:")}</strong>
                ${this.users.map((u) => u.username).join(", ")}
            </p>
            <ak-text-input
                name="reason"
                label=${msg("Reason")}
                autocomplete="off"
                placeholder=${msg("Reason for triggering the panic button")}
                help=${msg(
                    "A required explanation of why you are triggering the panic button. This will be included in audit logs and notifications.",
                )}
                required
            ></ak-text-input>
            <ak-switch-input
                name="notifyUser"
                label=${msg("Notify users")}
                ?checked=${this.defaultNotifyUser}
                help=${msg("Send email notification to the affected users.")}
            ></ak-switch-input>
            <ak-switch-input
                name="notifyAdmins"
                label=${msg("Notify admins")}
                ?checked=${this.defaultNotifyAdmins}
                help=${msg("Send email notification to all administrators.")}
            ></ak-switch-input>
            <ak-switch-input
                name="notifySecurity"
                label=${msg("Notify security")}
                ?checked=${this.defaultNotifySecurity}
                help=${msg("Send email notification to the security team.")}
            ></ak-switch-input>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-bulk-panic-button-form": UserBulkPanicButtonForm;
    }
}
