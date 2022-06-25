import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

import { KeyUnknown } from "../../../../elements/forms/Form";
import "../../../../elements/forms/HorizontalFormElement";
import { WizardFormPage } from "../../../../elements/wizard/WizardFormPage";

@customElement("ak-application-wizard-type-link")
export class TypeLinkApplicationWizardPage extends WizardFormPage {
    sidebarLabel = () => t`Application Link`;

    nextDataCallback = async (data: KeyUnknown): Promise<boolean> => {
        this.host.state["link"] = data.link;
        return true;
    };

    renderForm(): TemplateResult {
        return html`
            <form class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${t`Link`} ?required=${true} name="link">
                    <input type="text" value="" class="pf-c-form-control" required />
                    <p class="pf-c-form__helper-text">
                        ${t`URL which will be opened when a user clicks on the application.`}
                    </p>
                </ak-form-element-horizontal>
            </form>
        `;
    }
}
