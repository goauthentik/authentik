import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { Form } from "@goauthentik/elements/forms/Form";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { CertificateGenerationRequest, CertificateKeyPair, CryptoApi } from "@goauthentik/api";

@customElement("ak-crypto-certificate-generate-form")
export class CertificateKeyPairForm extends Form<CertificateGenerationRequest> {
    getSuccessMessage(): string {
        return msg("Successfully generated certificate-key pair.");
    }

    async send(data: CertificateGenerationRequest): Promise<CertificateKeyPair> {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsGenerateCreate({
            certificateGenerationRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${msg("Common Name")}
                name="commonName"
                ?required=${true}
            >
                <input type="text" class="pf-c-form-control" required />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Subject-alt name")} name="subjectAltName">
                <input class="pf-c-form-control" type="text" />
                <p class="pf-c-form__helper-text">
                    ${msg("Optional, comma-separated SubjectAlt Names.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Validity days")}
                name="validityDays"
                ?required=${true}
            >
                <input class="pf-c-form-control" type="number" value="365" />
            </ak-form-element-horizontal>
        </form>`;
    }
}
