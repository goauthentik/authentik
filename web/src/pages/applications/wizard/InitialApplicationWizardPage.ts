import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { WizardPage } from "../../../elements/wizard/WizardPage";

@customElement("ak-application-wizard-initial")
export class InitialApplicationWizardPage extends WizardPage {
    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFFormControl, PFFormControl, PFButton, AKGlobal, PFRadio];
    }

    sidebarLabel = () => t`Application details`;

    render(): TemplateResult {
        return html`
            <form class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                    <input
                        type="text"
                        value=""
                        class="pf-c-form-control"
                        required
                        @input=${(ev: InputEvent) => {
                            this._isValid = (ev.target as HTMLInputElement).value !== "";
                            this.host.requestUpdate();
                        }}
                    />
                    <p class="pf-c-form__helper-text">${t`Application's display Name.`}</p>
                </ak-form-element-horizontal>
                <ak-form-group>
                    <span slot="header"> ${t`Additional UI settings`} </span>
                    <div slot="body" class="pf-c-form">
                        <ak-form-element-horizontal label=${t`Publisher`} name="metaPublisher">
                            <input type="text" value="" class="pf-c-form-control" />
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal label=${t`Description`} name="metaDescription">
                            <textarea class="pf-c-form-control"></textarea>
                        </ak-form-element-horizontal>
                    </div>
                </ak-form-group>
            </form>
        `;
    }
}
