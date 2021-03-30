import { CertificateKeyPair, CryptoApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import "../../elements/Divider";

@customElement("ak-crypto-certificate-form")
export class CertificateKeyPairForm extends Form<CertificateKeyPair> {

    @property({attribute: false})
    keyPair?: CertificateKeyPair;

    getSuccessMessage(): string {
        if (this.keyPair) {
            return gettext("Successfully updated certificate-key pair.");
        } else {
            return gettext("Successfully created certificate-key pair.");
        }
    }

    send = (data: CertificateKeyPair): Promise<CertificateKeyPair> => {
        if (this.keyPair) {
            return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsPartialUpdate({
                kpUuid: this.keyPair.pk || "",
                data: data
            });
        } else {
            return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                name="name"
                ?required=${true}>
                <input type="text" value="${ifDefined(this.keyPair?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            ${this.keyPair ? html`<ak-divider>${gettext("Only change the fields below if you want to overwrite their values.")}</ak-divider>` : html``}
            <ak-form-element-horizontal
                label=${gettext("Certificate")}
                name="certificateData"
                ?required=${true}>
                <textarea class="pf-c-form-control" required>${ifDefined(this.keyPair?.certificateData)}</textarea>
                <p class="pf-c-form__helper-text">${gettext("PEM-encoded Certificate data.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                name="keyData"
                label=${gettext("Private Key")}>
                <textarea class="pf-c-form-control" >${ifDefined(this.keyPair?.keyData)}</textarea>
                <p class="pf-c-form__helper-text">${gettext("Optional Private Key. If this is set, you can use this keypair for encryption.")}</p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
