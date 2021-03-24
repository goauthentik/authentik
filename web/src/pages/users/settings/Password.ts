import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import AKGlobal from "../../../authentik.css";
import { gettext } from "django";
import { FlowURLManager } from "../../../api/legacy";

@customElement("ak-user-settings-password")
export class UserSettingsPassword extends LitElement {

    @property()
    stageId!: string;

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFButton, AKGlobal];
    }

    render(): TemplateResult {
        // For this stage we don't need to check for a configureFlow,
        // as the stage won't return any UI Elements if no configureFlow is set.
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">
                ${gettext('Change your password')}
            </div>
            <div class="pf-c-card__body">
                <a href="${FlowURLManager.configure(this.stageId, '?next=/%23user')}"
                    class="pf-c-button pf-m-primary">
                    ${gettext('Change password')}
                </a>
            </div>
        </div>`;
    }

}
