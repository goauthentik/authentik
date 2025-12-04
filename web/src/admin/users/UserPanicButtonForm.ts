import "#components/ak-switch-input";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { APIMessage } from "#elements/messages/Message";

import { AdminApi, CoreApi, UserPanicButtonRequest } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-user-panic-button-form")
export class UserPanicButtonForm extends Form<UserPanicButtonRequest> {
    @property({ type: Number })
    public instancePk?: number;

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
            message: msg(str`Panic button triggered successfully.`),
            description: msg("The user's account has been secured."),
        };
    }

    async send(data: UserPanicButtonRequest): Promise<void> {
        await new CoreApi(DEFAULT_CONFIG).coreUsersPanicButtonCreate({
            id: this.instancePk || 0,
            userPanicButtonRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`
            <p class="pf-c-form__helper-text" style="margin-bottom: 1rem; color: #c9190b;">
                ${msg(
                    "This action will lock the account, reset the password, and terminate all active sessions.",
                )}
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
                label=${msg("Notify user")}
                ?checked=${this.defaultNotifyUser}
                help=${msg("Send email notification to the affected user.")}
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
        "ak-user-panic-button-form": UserPanicButtonForm;
    }
}
