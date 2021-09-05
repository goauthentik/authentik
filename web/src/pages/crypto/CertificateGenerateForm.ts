import { CertificateGenerationRequest, CertificateKeyPair, CryptoApi } from "@goauthentik/api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-crypto-certificate-generate-form")
export class CertificateKeyPairForm extends Form<CertificateGenerationRequest> {
    getSuccessMessage(): string {
        return t`Successfully generated certificate-key pair.`;
    }

    send = (data: CertificateGenerationRequest): Promise<CertificateKeyPair> => {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsGenerateCreate({
            certificateGenerationRequest: data,
        });
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Common Name`} name="commonName" ?required=${true}>
                <input type="text" class="pf-c-form-control" required />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Subject-alt name`} name="subjectAltName">
                <input class="pf-c-form-control" type="text" />
                <p class="pf-c-form__helper-text">
                    ${t`Optional, comma-separated SubjectAlt Names.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Validity days`}
                name="validityDays"
                ?required=${true}
            >
                <input class="pf-c-form-control" type="number" value="365" />
            </ak-form-element-horizontal>
        </form>`;
    }
}
