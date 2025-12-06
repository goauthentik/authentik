import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { APIMessage } from "#elements/messages/Message";
import { getUserDisplayName } from "#elements/user/utils";

import { CoreApi, User, UserPanicButtonRequest } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-panic-button-form")
export class UserPanicButtonForm extends Form<UserPanicButtonRequest> {
    @property({ type: Number })
    public instancePk?: number;

    @property({ attribute: false })
    public user?: User;

    protected override formatAPISuccessMessage(): APIMessage | null {
        return {
            level: MessageLevel.success,
            message: msg(
                str`Panic button triggered for ${this.user ? getUserDisplayName(this.user) : "user"}`,
            ),
        };
    }

    async send(data: UserPanicButtonRequest): Promise<void> {
        await new CoreApi(DEFAULT_CONFIG).coreUsersPanicButtonCreate({
            id: this.instancePk || 0,
            userPanicButtonRequest: data,
        });
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    renderForm(): TemplateResult {
        return html`
            <ak-text-input
                name="reason"
                label=${msg("Reason")}
                autocomplete="off"
                placeholder=${msg("Reason for triggering panic button")}
                help=${msg(
                    "Locks account, resets password, and terminates all sessions. For more information, see docs at...",
                )}
                required
            ></ak-text-input>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-panic-button-form": UserPanicButtonForm;
    }
}
