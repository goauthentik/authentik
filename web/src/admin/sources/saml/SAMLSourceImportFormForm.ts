import "#admin/common/ak-flow-search/ak-flow-search-no-default";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import {
    FlowDesignationEnum,
    type SourcesSamlImportMetadataCreateRequest
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderForm(source: Partial<SourcesSamlImportMetadataCreateRequest> = {}) {
    return html`
        <ak-text-input
            name="name"
            label=${msg("Name")}
            .value=${source.name ?? ""}
            required
        ></ak-text-input>
        <ak-form-element-horizontal
            label=${msg("Pre-authentication flow")}
            required
            name="preAuthenticationFlow"
        >
            <ak-flow-search-no-default
            flowType=${FlowDesignationEnum.StageConfiguration}
            required
            ></ak-flow-search-no-default>
            <p class="pf-c-form__helper-text">
                ${msg("Flow used before redirecting to this identity provider.")}
            </p>
        </ak-form-element-horizontal>

        <ak-form-element-horizontal label=${msg("Metadata")} name="file" required>
            <input type="file" value="" class="pf-c-form-control" required accept=".xml" />
            <p class="pf-c-form__helper-text">
                ${msg("SAML metadata XML file to import source settings from.")}
            </p>
        </ak-form-element-horizontal>
    `;
}
