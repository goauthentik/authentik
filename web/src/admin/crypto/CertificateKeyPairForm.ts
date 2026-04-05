import "#components/ak-secret-textarea-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import { CertificateKeyPair, CertificateKeyPairRequest, CryptoApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-crypto-certificate-form")
export class CertificateKeyPairForm extends ModelForm<CertificateKeyPair, string> {
    loadInstance(pk: string): Promise<CertificateKeyPair> {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsRetrieve({
            kpUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated certificate-key pair.")
            : msg("Successfully created certificate-key pair.");
    }

    async send(data: CertificateKeyPair): Promise<CertificateKeyPair> {
        if (this.instance) {
            return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsPartialUpdate({
                kpUuid: this.instance.pk || "",
                patchedCertificateKeyPairRequest: data,
            });
        }
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsCreate({
            certificateKeyPairRequest: data as unknown as CertificateKeyPairRequest,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} name="name" required>
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-secret-textarea-input
                label=${msg("Certificate")}
                name="certificateData"
                input-hint="code"
                placeholder="-----BEGIN CERTIFICATE-----"
                ?required=${!this.instance}
                ?revealed=${!this.instance}
                help=${msg("PEM-encoded Certificate data.")}
            ></ak-secret-textarea-input>
            <ak-secret-textarea-input
                label=${msg("Private Key")}
                name="keyData"
                input-hint="code"
                ?revealed=${!this.instance}
                help=${msg(
                    "Optional Private Key. If this is set, you can use this keypair for encryption.",
                )}
            ></ak-secret-textarea-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-crypto-certificate-form": CertificateKeyPairForm;
    }
}
