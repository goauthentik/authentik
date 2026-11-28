import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import { AKCertificateSearch } from "#admin/common/AKCertificateSearch";
import { XMLSigningKeyTypes } from "#admin/common/certificate-key-types";
import {
    AKSourceAuthenticationFlowField,
    AKSourceEnrollmentFlowField,
    AKSourcePreAuthenticationFlowField,
} from "#admin/sources/components/flow-fields";

import { type SourcesSamlImportMetadataCreateRequest } from "@goauthentik/api";

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
        ${AKSourcePreAuthenticationFlowField({
            help: msg("Flow used before redirecting to this identity provider."),
        })}
        <ak-form-element-horizontal label=${msg("Metadata")} name="file" required>
            <input type="file" value="" class="pf-c-form-control" required accept=".xml" />
            <p class="pf-c-form__helper-text">
                ${msg("SAML metadata XML file to import source settings from.")}
            </p>
        </ak-form-element-horizontal>
        <div class="pf-c-form__group">
            <div class="pf-c-form__group-label">
                <div class="pf-c-form__label">
                    <span class="pf-c-form__label-text">
                        ${msg("Signature verification target")}
                    </span>
                </div>
            </div>

            <div class="pf-c-form__group-control">
                <ak-switch-input
                    name="signedAssertion"
                    label=${msg("Verify Assertion Signature")}
                    ?checked=${true}
                    help=${msg(
                        "When enabled, authentik will look for a Signature inside of the Assertion element.",
                    )}
                ></ak-switch-input>
                <ak-switch-input
                    name="signedResponse"
                    label=${msg("Verify Response Signature")}
                    ?checked=${false}
                    help=${msg(
                        "When enabled, authentik will look for a Signature inside of the Response element.",
                    )}
                ></ak-switch-input>
            </div>
        </div>
        <ak-form-element-horizontal label=${msg("Signing keypair")} name="signingKp">
            ${AKCertificateSearch({ name: "signingKp", allowedKeyTypes: XMLSigningKeyTypes })}
            <p class="pf-c-form__helper-text">
                ${msg("Optional. Keypair used to sign outgoing requests.")}
            </p>
        </ak-form-element-horizontal>
        ${AKSourceAuthenticationFlowField({
            help: msg("Flow to use when authenticating existing users."),
        })}
        ${AKSourceEnrollmentFlowField({ help: msg("Flow to use when enrolling new users.") })}
    `;
}
