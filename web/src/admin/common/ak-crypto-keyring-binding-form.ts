import "#admin/common/ak-crypto-certificate-search";
import "#elements/forms/HorizontalFormElement";

import { AKElement } from "#elements/Base";

import type { AkCryptoCertificateSearch } from "#admin/common/ak-crypto-certificate-search";

import { CertificateKeyPair, KeyTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

export type BindingDraft = {
    keypair: string | null;
    order: number;
};

@customElement("ak-crypto-keyring-binding-form")
export class AkCryptoKeyringBindingForm extends AKElement {
    @property({ type: Number })
    order = 0;

    @property({ type: String })
    keypair: string | null = null;

    @property({ type: Boolean, attribute: "require-key" })
    requireKey = false;

    @property({ type: Array, attribute: "allowed-key-types" })
    allowedKeyTypes?: KeyTypeEnum[];

    // ★ “静的 exclude” 前提：動的更新しなくていい
    @property({ type: Array, attribute: "exclude-keypairs" })
    excludeKeypairs: string[] = [];

    @state()
    private draft: BindingDraft = { keypair: null, order: 0 };

    connectedCallback(): void {
        super.connectedCallback();
        this.draft = { keypair: this.keypair, order: this.order };
    }

    public buildDraft(): BindingDraft {
        return { keypair: this.draft.keypair, order: Number(this.draft.order ?? 0) };
    }

    render(): TemplateResult {
        return html`
            <div class="pf-c-form">
                <ak-form-element-horizontal label=${msg("Order")} name="order" required>
                    <input
                        class="pf-c-form-control"
                        type="number"
                        min="0"
                        .value=${String(this.draft.order)}
                        @input=${(ev: InputEvent) => {
                            const t = ev.target as HTMLInputElement;
                            this.draft = { ...this.draft, order: Number(t.value ?? "0") };
                        }}
                        required
                    />
                </ak-form-element-horizontal>
                <ak-form-element-horizontal label=${msg("Certificate")} name="keypair" required>
                    <ak-crypto-certificate-search
                        .certificate=${this.draft.keypair}
                        ?nokey=${!this.requireKey}
                        .allowedKeyTypes=${this.allowedKeyTypes ?? []}
                        .excludeKeypairs=${this.excludeKeypairs}
                        include-details
                        @input=${(ev: InputEvent) => {
                            const target = ev.target as AkCryptoCertificateSearch;
                            const kp = (
                                target as unknown as { selectedKeypair?: CertificateKeyPair }
                            ).selectedKeypair;
                            this.draft = { ...this.draft, keypair: kp?.pk ?? null };
                        }}
                    ></ak-crypto-certificate-search>
                </ak-form-element-horizontal>

                <p class="pf-c-form__helper-text">
                    ${this.requireKey
                        ? msg("Only keypairs with a private key are allowed.")
                        : msg("Certificate-only keypairs are allowed.")}
                </p>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-crypto-keyring-binding-form": AkCryptoKeyringBindingForm;
    }
}
