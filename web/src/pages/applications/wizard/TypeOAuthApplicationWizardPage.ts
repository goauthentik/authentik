import { t } from "@lingui/macro";

import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { CSSResult, TemplateResult, html } from "lit";

import AKGlobal from "../../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFRadio from "@patternfly/patternfly/components/Radio/radio.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import "../../../elements/forms/HorizontalFormElement";
import { WizardPage } from "../../../elements/wizard/WizardPage";

@customElement("ak-application-wizard-type-oauth")
export class TypeOAuthApplicationWizardPage extends WizardPage {
    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFFormControl, PFFormControl, PFButton, AKGlobal, PFRadio];
    }

    sidebarLabel = () => t`Application type`;

    render(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            - web application - single-page application - API
        </form> `;
    }
}
