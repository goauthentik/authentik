import "@goauthentik/elements/forms/HorizontalFormElement";
import { WizardPage } from "@goauthentik/elements/wizard/WizardPage";

import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-application-wizard-type-oauth-api")
export class TypeOAuthAPIApplicationWizardPage extends WizardPage {
    static get styles(): CSSResult[] {
        return [PFBase, PFButton, PFForm, PFRadio];
    }

    sidebarLabel = () => t`Method details`;

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <p>
                ${t`This configuration can be used to authenticate to authentik with other APIs other otherwise programmatically.`}
            </p>
            <p>
                ${t`By default, all service accounts can authenticate as this application, as long as they have a valid token of the type app-password.`}
            </p>
        </form> `;
    }
}
