import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/ak-secret-textarea-input.js";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
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

    renderForm(): TemplateResult {
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
                required
                ?revealed=${this.instance === undefined}
                help=${msg("PEM-encoded Certificate data.")}
            ></ak-secret-textarea-input>
            <ak-secret-textarea-input
                label=${msg("Private Key")}
                name="keyData"
                input-hint="code"
                ?revealed=${this.instance === undefined}
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
