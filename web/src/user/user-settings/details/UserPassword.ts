import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { CSSResult, LitElement } from "lit";
import { customElement } from "lit/decorators";
import { property } from "lit/decorators";
import { ifDefined } from "lit/directives/if-defined";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-user-settings-password")
export class UserSettingsPassword extends LitElement {
    @property()
    objectId!: string;

    @property()
    configureUrl?: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, PFForm, PFFormControl, AKGlobal];
    }

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
