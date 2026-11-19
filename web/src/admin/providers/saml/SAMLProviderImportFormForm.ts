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

        <ak-form-element-horizontal label=${msg("Metadata")} name="file">
            <input type="file" value="" class="pf-c-form-control" accept=".xml" />
            <p class="pf-c-form__helper-text">
                ${msg(
                    "SAML metadata XML file to import provider settings from. Leave empty to use a metadata URL instead.",
                )}
            </p>
        </ak-form-element-horizontal>

        <ak-text-input
            name="url"
            label=${msg("Metadata URL")}
            placeholder=${msg("https://...")}
            input-hint="code"
            inputmode="url"
            value=${provider.url ?? ""}
            help=${msg(
                "URL to download the SAML metadata from. The provider's settings will be kept up to date from this URL periodically.",
            )}
        ></ak-text-input>
    `;
}
