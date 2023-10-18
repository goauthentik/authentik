import "@goauthentik/admin/common/ak-flow-search/ak-flow-search-no-default";
import "@goauthentik/components/ak-file-input";
import { AkFileInput } from "@goauthentik/components/ak-file-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { customElement } from "@lit/reactive-element/decorators/custom-element.js";
import { html } from "lit";
import { query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    FlowsInstancesListDesignationEnum,
    ProvidersSamlImportMetadataCreateRequest,
} from "@goauthentik/api";

import BaseProviderPanel from "../BaseProviderPanel";

@customElement("ak-application-wizard-authentication-by-saml-import")
export class ApplicationWizardProviderSamlImport extends BaseProviderPanel {
    @query('ak-file-input[name="metadata"]')
    fileInput!: AkFileInput;

    handleChange(ev: InputEvent) {
        if (!ev.target) {
            console.warn(`Received event with no target: ${ev}`);
            return;
        }
        const target = ev.target as HTMLInputElement;
        if (target.type === "file") {
            const file = this.fileInput.files?.[0] ?? null;
            if (file) {
                this.dispatchWizardUpdate({
                    update: {
                        provider: {
                            file,
                        },
                    },
                    status: this.form.checkValidity() ? "valid" : "invalid",
                });
            }
            return;
        }
        super.handleChange(ev);
    }

    render() {
        const provider = this.wizard.provider as
            | ProvidersSamlImportMetadataCreateRequest
            | undefined;

        return html` <form class="pf-c-form pf-m-horizontal" @input=${this.handleChange}>
            <ak-text-input
                name="name"
                value=${ifDefined(provider?.name)}
                label=${msg("Name")}
                required
                help=${msg("Method's display Name.")}
            ></ak-text-input>

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
