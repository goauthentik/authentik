import "#components/ak-text-input";
import "#components/ak-number-input";
import "#elements/forms/Radio";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { Form } from "#elements/forms/Form";
import { RadioChangeEventDetail } from "#elements/forms/Radio";

import {
    AlgEnum,
    CertificateGenerationRequest,
    CertificateKeyPair,
    CryptoApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-crypto-certificate-generate-form")
export class CryptoCertificateGenerateForm extends Form<CertificateGenerationRequest> {
    public static override verboseName = msg("Certificate-Key Pair");
    public static override verboseNamePlural = msg("Certificate-Key Pairs");
    public static override createLabel = msg("Generate");
    public static override submitVerb = msg("Generate");

    @state()
    protected alg: AlgEnum = AlgEnum.Rsa;

    #algChangeListener = (event: CustomEvent<RadioChangeEventDetail<AlgEnum>>) => {
        this.alg = event.detail.value;
    };

    getSuccessMessage(): string {
        return msg("Successfully generated certificate-key pair.");
    }

    async send(data: CertificateGenerationRequest): Promise<CertificateKeyPair> {
        return aki(CryptoApi).cryptoCertificatekeypairsGenerateCreate({
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
                    @change=${this.#algChangeListener}
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
                        {
                            label: msg("ML-DSA-44", { id: "crypto.generate.alg.ml-dsa-44.label" }),
                            value: AlgEnum.Mldsa44,
                        },
                        {
                            label: msg("ML-DSA-65", { id: "crypto.generate.alg.ml-dsa-65.label" }),
                            value: AlgEnum.Mldsa65,
                        },
                        {
                            label: msg("ML-DSA-87", { id: "crypto.generate.alg.ml-dsa-87.label" }),
                            value: AlgEnum.Mldsa87,
                        },
                    ]}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${msg("Algorithm used to generate the private key.")}
                </p>
            </ak-form-element-horizontal>
            ${this.renderKeySize()}`;
    }

    /**
     * Only RSA and ECDSA have a selectable key size, every other algorithm has a fixed one.
     *
     * Each algorithm renders its own template so the selection resets to that algorithm's
     * default when switching between them.
     */
    protected renderKeySize(): TemplateResult | typeof nothing {
        if (this.alg === AlgEnum.Rsa) {
            return html`<ak-form-element-horizontal
                label=${msg("Key size")}
                required
                name="keySize"
            >
                <ak-radio
                    .options=${[
                        { label: msg("2048 bits"), value: 2048 },
                        { label: msg("3072 bits"), value: 3072 },
                        { label: msg("4096 bits"), value: 4096, default: true },
                    ]}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">${msg("Size of the RSA private key.")}</p>
            </ak-form-element-horizontal>`;
        }

        if (this.alg === AlgEnum.Ecdsa) {
            return html`<ak-form-element-horizontal label=${msg("Curve")} required name="keySize">
                <ak-radio
                    .options=${[
                        { label: msg("P-256"), value: 256, default: true },
                        { label: msg("P-384"), value: 384 },
                        { label: msg("P-521"), value: 521 },
                    ]}
                >
                </ak-radio>
                <p class="pf-c-form__helper-text">
                    ${msg("Elliptic curve used to generate the ECDSA private key.")}
                </p>
            </ak-form-element-horizontal>`;
        }

        return nothing;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-crypto-certificate-generate-form": CryptoCertificateGenerateForm;
    }
}
