import { customElement, html, TemplateResult } from "lit-element";
import { t } from "@lingui/macro";
import { BaseUserSettings } from "../BaseUserSettings";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-user-settings-password")
export class UserSettingsPassword extends BaseUserSettings {
    render(): TemplateResult {
        // For this stage we don't need to check for a configureFlow,
        // as the stage won't return any UI Elements if no configureFlow is set.
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">${t`Change your password`}</div>
            <div class="pf-c-card__body">
                <a href="${ifDefined(this.configureUrl)}" class="pf-c-button pf-m-primary">
                    ${t`Change password`}
                </a>
            </div>
        </div>`;
    }
}
