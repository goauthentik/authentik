import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";
import { property } from "lit/decorators.js";

import AKGlobal from "../../../authentik.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../../../elements/forms/HorizontalFormElement";
import { WizardPage } from "../../../elements/wizard/WizardPage";

@customElement("ak-application-wizard-type-link")
export class TypeLinkApplicationWizardPage extends WizardPage {
    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFFormControl, PFFormControl, AKGlobal, PFRadio];
    }

    @property()
    link?: string;

    sidebarLabel = () => t`Application Link`;

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Link`} ?required=${true} name="link">
                <input
                    type="text"
                    value=""
                    class="pf-c-form-control"
                    required
                    @input=${(ev: InputEvent) => {
                        const value = (ev.target as HTMLInputElement).value;
                        this._isValid = value !== "";
                        this.link = value;
                        this.host.state["link"] = this.link;
                        this.host.requestUpdate();
                    }}
                />
                <p class="pf-c-form__helper-text">
                    ${t`URL which will be opened when a user clicks on the application.`}
                </p>
            </ak-form-element-horizontal>
        </form> `;
    }
}
