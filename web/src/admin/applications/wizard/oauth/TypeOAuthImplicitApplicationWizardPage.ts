import "@goauthentik/elements/forms/HorizontalFormElement";
import { WizardFormPage } from "@goauthentik/elements/wizard/WizardFormPage";

import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { TemplateResult, html } from "lit";

@customElement("ak-application-wizard-type-oauth-implicit")
export class TypeOAuthImplicitApplicationWizardPage extends WizardFormPage {
    sidebarLabel = () => t`Method details`;

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">some stuff idk</form> `;
    }
}
