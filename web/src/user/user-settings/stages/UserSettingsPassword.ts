import { t } from "@lingui/macro";

import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators";
import { ifDefined } from "lit/directives/if-defined";

import { BaseUserSettings } from "../BaseUserSettings";

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
