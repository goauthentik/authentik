import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import {
    AKAuthorizationFlowField,
    AKInvalidationFlowField,
} from "#admin/providers/components/flow-fields";

import { type ProvidersSamlImportMetadataCreateRequest } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function renderForm(provider: Partial<ProvidersSamlImportMetadataCreateRequest> = {}) {
    return html`
        <ak-text-input
            name="name"
            label=${msg("Provider Name")}
            placeholder=${msg("Type a provider name...")}
            spellcheck="false"
            value=${provider.name ?? ""}
            required
        ></ak-text-input>

        ${AKAuthorizationFlowField({})} ${AKInvalidationFlowField({ defaultFlowSlug: null })}

        <ak-form-element-horizontal label=${msg("Metadata")} name="file" required>
            <input type="file" value="" class="pf-c-form-control" required accept=".xml" />
            <p class="pf-c-form__helper-text">
                ${msg("SAML metadata XML file to import provider settings from.")}
            </p>
        </ak-form-element-horizontal>
    `;
}
