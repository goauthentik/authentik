import { KeyUnknown } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { WizardFormPage } from "@goauthentik/elements/wizard/WizardFormPage";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

@customElement("ak-application-wizard-type-link")
export class TypeLinkApplicationWizardPage extends WizardFormPage {
    sidebarLabel = () => msg("Application Link");

    nextDataCallback = async (data: KeyUnknown): Promise<boolean> => {
        this.host.state["link"] = data.link;
        return true;
    };

    renderForm(): TemplateResult {
        return html`
            <form class="pf-c-form pf-m-horizontal">
                <ak-form-element-horizontal label=${msg("Link")} ?required=${true} name="link">
                    <input type="text" value="" class="pf-c-form-control" required />
                    <p class="pf-c-form__helper-text">
                        ${msg("URL which will be opened when a user clicks on the application.")}
                    </p>
                </ak-form-element-horizontal>
            </form>
        `;
    }
}
