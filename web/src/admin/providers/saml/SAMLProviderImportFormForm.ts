import "#admin/common/ak-flow-search/ak-flow-search-no-default";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import {
    FlowsInstancesListDesignationEnum,
    type ProvidersSamlImportMetadataCreateRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderForm(provider: Partial<ProvidersSamlImportMetadataCreateRequest> = {}) {
    return html`
        <ak-text-input
            name="name"
            label=${msg("Name")}
            .value=${provider.name ?? ""}
            required
        ></ak-text-input>

        <ak-form-element-horizontal
            label=${msg("Authorization flow")}
            required
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

        <ak-form-element-horizontal
            label=${msg("Invalidation flow")}
            required
            name="invalidationFlow"
        >
            <ak-flow-search-no-default
                flowType=${FlowsInstancesListDesignationEnum.Invalidation}
                required
            ></ak-flow-search-no-default>
            <p class="pf-c-form__helper-text">
                ${msg("Flow used when logging out of this provider.")}
            </p>
        </ak-form-element-horizontal>

        <ak-form-element-horizontal label=${msg("Metadata")} name="file" required>
            <input type="file" value="" class="pf-c-form-control" required accept=".xml" />
            <p class="pf-c-form__helper-text">
                ${msg("SAML metadata XML file to import provider settings from.")}
            </p>
        </ak-form-element-horizontal>
    `;
}
