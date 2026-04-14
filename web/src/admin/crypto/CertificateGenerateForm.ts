import "#components/ak-text-input";
import "#components/ak-number-input";
import "#elements/forms/Radio";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";

import {
    AlgEnum,
    CertificateGenerationRequest,
    CertificateKeyPair,
    CryptoApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-crypto-certificate-generate-form")
export class CryptoCertificateGenerateForm extends Form<CertificateGenerationRequest> {
    public static override verboseName = msg("Certificate-Key Pair");
    public static override verboseNamePlural = msg("Certificate-Key Pairs");
    public static override createLabel = msg("Generate");
    public static override submitVerb = msg("Generate");

    getSuccessMessage(): string {
        return msg("Successfully generated certificate-key pair.");
    }

    async send(data: CertificateGenerationRequest): Promise<CertificateKeyPair> {
        return new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsGenerateCreate({
            certificateGenerationRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                label=${msg("Common Name")}
                name="commonName"
                required
                placeholder=${msg("Type a name for this certificate...")}
                autofocus
                autocomplete="off"
                spellcheck="false"
            ></ak-text-input>
            <ak-text-input
                label=${msg("Subject-alt name")}
                name="subjectAltName"
                autocomplete="off"
                input-hint="code"
                help=${msg("Optional, comma-separated SubjectAlt Names.")}
                placeholder=${msg("e.g. mydomain.com, *.mydomain.com, mydomain.local")}
            ></ak-text-input>

            <ak-number-input
                label=${msg("Validity days")}
                name="validityDays"
                required
                value="365"
            ></ak-number-input>

            <ak-form-element-horizontal label=${msg("Private key Algorithm")} required name="alg">
                <ak-radio
                    .options=${[
                        {
                            label: msg("RSA"),
                            value: AlgEnum.Rsa,
                            default: true,
                        },
                        {
                            label: msg("ECDSA"),
                            value: AlgEnum.Ecdsa,
                        },
                        {
                            label: msg("ED25519"),
                            value: AlgEnum.Ed25519,
                        },
                        {
                            label: msg("ED448"),
                            value: AlgEnum.Ed448,
                        },
                    ]}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${msg("Algorithm used to generate the private key.")}
                </p>
            </ak-form-element-horizontal> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-crypto-certificate-generate-form": CryptoCertificateGenerateForm;
    }
}
