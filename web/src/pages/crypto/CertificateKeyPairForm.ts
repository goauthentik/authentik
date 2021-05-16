import { CertificateKeyPair, CryptoApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";
import { ModelForm } from "../../elements/forms/ModelForm";

@customElement("ak-crypto-certificate-form")
export class CertificateKeyPairForm extends ModelForm<CertificateKeyPair, string> {

    loadInstance(pk: string): Promise<CertificateKeyPair> {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsRetrieve({
            kpUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated certificate-key pair.`;
        } else {
            return t`Successfully created certificate-key pair.`;
        }
    }

    send = (data: CertificateKeyPair): Promise<CertificateKeyPair> => {
        if (this.instance) {
            return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsPartialUpdate({
                kpUuid: this.instance.pk || "",
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
                label=${t`Name`}
                name="name"
                ?required=${true}>
                <input type="text" value="${ifDefined(this.instance?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Certificate`}
                name="certificateData"
                ?writeOnly=${this.instance !== undefined}
                ?required=${true}>
                <textarea class="pf-c-form-control" required>${ifDefined(this.instance?.certificateData)}</textarea>
                <p class="pf-c-form__helper-text">${t`PEM-encoded Certificate data.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                name="keyData"
                ?writeOnly=${this.instance !== undefined}
                label=${t`Private Key`}>
                <textarea class="pf-c-form-control" >${ifDefined(this.instance?.keyData)}</textarea>
                <p class="pf-c-form__helper-text">${t`Optional Private Key. If this is set, you can use this keypair for encryption.`}</p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
