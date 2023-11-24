import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { dateTimeLocal, first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";

import { AdminApi, Settings } from "@goauthentik/api";

@customElement("ak-admin-settings-form")
export class AdminSettingsForm extends ModelForm<Settings, string> {

    async loadInstance(pk: string): Promise<Settings> {
        return await new AdminApi(DEFAULT_CONFIG).adminSettingsRetrieve();
    }

    getSuccessMessage(): string {
        return msg("Successfully updated settings.");
    }

    async send(data: Settings): Promise<Settings> {
        return new AdminApi(DEFAULT_CONFIG).adminSettingsUpdate({
            settingsRequest: data
        });
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal
                label=${msg("Avatars")}
                name="avatars"
                ?required=${true}
            >
                <input
                    type="text"
                    value="${this.instance?.avatars}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Configure how authentik should show avatars for users.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}
