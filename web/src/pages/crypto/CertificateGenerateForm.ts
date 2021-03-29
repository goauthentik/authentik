import { CertificateGeneration, CryptoApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-crypto-certificate-generate-form")
export class CertificateKeyPairForm extends Form<CertificateGeneration> {

    getSuccessMessage(): string {
        return gettext("Successfully generated certificate-key pair.");
    }

    send = (data: CertificateGeneration): Promise<CertificateGeneration> => {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsGenerate({
            data: data
        });
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${gettext("Common Name")} ?required=${true}>
                <input type="text" name="commonName" class="pf-c-form-control" required="">
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${gettext("Subject-alt name")}>
                <input class="pf-c-form-control" type="text" name="subjectAltName">
                <p class="pf-c-form__helper-text">${gettext("Optional, comma-separated SubjectAlt Names.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${gettext("Validity days")} ?required=${true}>
                <input class="pf-c-form-control" type="number" name="validityDays" value="365">
            </ak-form-element-horizontal>
        </form>`;
    }

}
