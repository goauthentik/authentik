import "@goauthentik/elements/forms/HorizontalFormElement";
import { WizardFormPage } from "@goauthentik/elements/wizard/WizardFormPage";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

@customElement("ak-application-wizard-type-oauth-implicit")
export class TypeOAuthImplicitApplicationWizardPage extends WizardFormPage {
    sidebarLabel = () => msg("Method details");

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">some stuff idk</form> `;
    }
}
