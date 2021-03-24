import { customElement, html, TemplateResult } from "lit-element";
import { gettext } from "django";
import { FlowURLManager } from "../../../api/legacy";
import { BaseUserSettings } from "./BaseUserSettings";

@customElement("ak-user-settings-password")
export class UserSettingsPassword extends BaseUserSettings {

    render(): TemplateResult {
        // For this stage we don't need to check for a configureFlow,
        // as the stage won't return any UI Elements if no configureFlow is set.
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">
                ${gettext("Change your password")}
            </div>
            <div class="pf-c-card__body">
                <a href="${FlowURLManager.configure(this.objectId, "?next=/%23%2Fuser")}"
                    class="pf-c-button pf-m-primary">
                    ${gettext("Change password")}
                </a>
            </div>
        </div>`;
    }

}
