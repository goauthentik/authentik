import "#admin/common/ak-flow-search/ak-flow-search-no-default";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { AKLabel } from "#components/ak-label";

import {
    FlowDesignationEnum,
    type ProvidersSamlImportMetadataCreateRequest,
} from "@goauthentik/api";

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

        <ak-form-element-horizontal required name="authorizationFlow">
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                    htmlFor: "authorizationFlow",
                    required: true,
                },
                msg("Authorization Flow"),
            )}
            <ak-flow-search-no-default
                id="authorizationFlow"
                flowType=${FlowDesignationEnum.Authorization}
                required
            ></ak-flow-search-no-default>
            <p class="pf-c-form__helper-text">
                ${msg("Flow used when authorizing this provider.")}
            </p>
        </ak-form-element-horizontal>

        <ak-form-element-horizontal required name="invalidationFlow">
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                    htmlFor: "invalidationFlow",
                    required: true,
                },
                msg("Invalidation Flow"),
            )}
            <ak-flow-search-no-default
                id="invalidationFlow"
                flowType=${FlowDesignationEnum.Invalidation}
                required
            ></ak-flow-search-no-default>
            <p class="pf-c-form__helper-text">
                ${msg("Flow used when logging out of this provider.")}
            </p>
        </ak-form-element-horizontal>

        <ak-form-element-horizontal name="file" required>
            ${AKLabel(
                {
                    slot: "label",
                    className: "pf-c-form__group-label",
                    htmlFor: "file",
                    required: true,
                },
                msg("Metadata"),
            )}
            <input
                id="file"
                type="file"
                value=""
                class="pf-c-form-control"
                required
                accept=".xml"
            />
            <p class="pf-c-form__helper-text">
                ${msg("SAML metadata XML file to import provider settings from.")}
            </p>
        </ak-form-element-horizontal>
    `;
}
