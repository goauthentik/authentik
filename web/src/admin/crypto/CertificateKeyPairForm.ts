import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { CertificateKeyPair, CertificateKeyPairRequest, CryptoApi } from "@goauthentik/api";

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

    async send(data: CertificateKeyPair): Promise<CertificateKeyPair> {
        if (this.instance) {
            return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsPartialUpdate({
                kpUuid: this.instance.pk || "",
                patchedCertificateKeyPairRequest: data,
            });
        } else {
            return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsCreate({
                certificateKeyPairRequest: data as unknown as CertificateKeyPairRequest,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} name="name" ?required=${true}>
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Certificate`}
                name="certificateData"
                ?writeOnly=${this.instance !== undefined}
                ?required=${true}
            >
                <textarea class="pf-c-form-control" required></textarea>
                <p class="pf-c-form__helper-text">${t`PEM-encoded Certificate data.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                name="keyData"
                ?writeOnly=${this.instance !== undefined}
                label=${t`Private Key`}
            >
                <textarea class="pf-c-form-control"></textarea>
                <p class="pf-c-form__helper-text">
                    ${t`Optional Private Key. If this is set, you can use this keypair for encryption.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
