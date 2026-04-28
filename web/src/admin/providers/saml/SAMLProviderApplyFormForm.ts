import "#admin/common/ak-crypto-certificate-search";
import "#elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";

export function renderForm(): TemplateResult {
    return html`
        <div class="pf-c-form">
            <ak-form-element-horizontal label=${msg("Metadata file")} required>
                <input
                    class="pf-c-form-control"
                    type="file"
                    name="file"
                    accept=".xml,application/xml,text/xml"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Select the SAML SP metadata XML file to apply to this provider.")}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal
                name="signingCertificate"
                label=${msg("Trust anchor certificate")}
            >
                <ak-crypto-certificate-search nokey></ak-crypto-certificate-search>
                <p class="pf-c-form__helper-text">
                    ${msg("Optional. If set, verify the metadata using this certificate.")}
                </p>
            </ak-form-element-horizontal>

            <p class="pf-c-form__helper-text">
                ${msg(
                    "If the metadata is unsigned, it will be accepted. If it is signed and verification fails, the apply will be rejected.",
                )}
            </p>
        </div>
    `;
}
