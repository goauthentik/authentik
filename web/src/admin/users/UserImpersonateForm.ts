import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { APIMessage, MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";

import { AdminApi, CoreApi, ImpersonationRequest } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("ak-user-impersonate-form")
export class UserImpersonateForm extends Form<ImpersonationRequest> {
    @property({ type: Number })
    public instancePk?: number;

    @state()
    private requireReason = false;

    async firstUpdated(): Promise<void> {
        try {
            const settings = await new AdminApi(DEFAULT_CONFIG).adminSettingsRetrieve();
            this.requireReason = settings.impersonationRequireReason ?? false;
        } catch (error) {
            console.error("Failed to fetch impersonation settings:", error);
            // fallback to reason not required as the backend will still validate it
            this.requireReason = false;
        }
    }

    protected override formatAPISuccessMessage(): APIMessage | null {
        return {
            level: MessageLevel.success,
            message: msg(str`Impersonating user...`),
            description: msg("This may take a few seconds."),
        };
    }

    async send(data: ImpersonationRequest): Promise<void> {
        return new CoreApi(DEFAULT_CONFIG)
            .coreUsersImpersonateCreate({
                id: this.instancePk || 0,
                impersonationRequest: data,
            })
            .then(() => {
                window.location.reload();
            });
    }

    renderForm(): TemplateResult {
        return html`<ak-text-input
            name="reason"
            label=${msg("Reason")}
            autocomplete="off"
            placeholder=${msg("Reason for impersonating the user")}
            help=${msg(
                "A brief explanation of why you are impersonating the user. This will be included in audit logs.",
            )}
            ?required=${this.requireReason}
        ></ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-impersonate-form": UserImpersonateForm;
    }
}
