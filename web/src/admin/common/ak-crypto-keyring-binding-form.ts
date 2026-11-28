import "#elements/forms/HorizontalFormElement";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

import { AKElement } from "#elements/Base";

import { AKCertificateSearch } from "#admin/common/AKCertificateSearch";

import { KeyTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

export type BindingDraft = {
    keypair: string | null;
    order: number;
};

@customElement("ak-crypto-keyring-binding-form")
export class AkCryptoKeyringBindingForm extends AKElement {
    static styles: CSSResult[] = [PFForm, PFFormControl];

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
                    ${AKCertificateSearch({
                        name: "keypair",
                        value: this.draft.keypair,
                        noKey: !this.requireKey,
                        allowedKeyTypes: this.allowedKeyTypes ?? [],
                        excludeKeypairs: this.excludeKeypairs,
                        onChange: (ev) => {
                            this.draft = { ...this.draft, keypair: ev.detail.value?.pk ?? null };
                        },
                    })}
                </ak-form-element-horizontal>

                <p class="pf-c-form__helper-text">
                    ${
                        this.requireKey
                            ? msg("Only keypairs with a private key are allowed.")
                            : msg("Certificate-only keypairs are allowed.")
                    }
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
