import "@goauthentik/admin/common/ak-flow-search/ak-flow-search-no-default";
import "@goauthentik/components/ak-file-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";

import { FlowsInstancesListDesignationEnum } from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-saml-import")
export class ApplicationWizardProviderSamlImport extends BaseProviderPanel {
    render() {
        return html` <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input name="name" label=${msg("Name")} required></ak-text-input>

            <ak-form-element-horizontal
                label=${msg("Authorization flow")}
                ?required=${true}
                name="authorizationFlow"
            >
                <ak-flow-search-no-default
                    flowType=${FlowsInstancesListDesignationEnum.Authorization}
                    required
                ></ak-flow-search-no-default>
                <p class="pf-c-form__helper-text">
                    ${msg("Flow used when authorizing this provider.")}
                </p>
            </ak-form-element-horizontal>

            <ak-file-input name="metadata" label=${msg("Metadata")} required></ak-file-input>
        </form>`;
    }
}

export default ApplicationWizardProviderSamlImport;
