import "#elements/EmptyState";
import "#admin/common/ak-crypto-keyring-manager";

import { Form } from "#elements/forms/Form";

import type { AkCryptoKeyringManager } from "#admin/common/ak-crypto-keyring-manager";

import type { CertificateKeyPairRing, KeyTypeEnum } from "@goauthentik/api";

import type { PropertyValues } from "lit";
import { html, TemplateResult } from "lit";
import { customElement, property, query } from "lit/decorators.js";

/**
 * Wrap AkCryptoKeyringManager so it can be hosted inside <ak-forms-modal slot="form">.
 * This avoids "No form found" and makes modal rendering consistent.
 */
@customElement("ak-crypto-keyring-manager-form")
export class AkCryptoKeyringManagerForm extends Form<CertificateKeyPairRing> {
    @property({ type: String, attribute: "ring-uuid" })
    ringUuid?: string;

    @property({ type: Boolean, attribute: "require-key" })
    requireKey = false;

    @property({ type: Array, attribute: "allowed-key-types" })
    allowedKeyTypes?: KeyTypeEnum[];

    @query("ak-crypto-keyring-manager")
    private manager?: AkCryptoKeyringManager;

    // Optional: keep manager updated if ringUuid changes while modal is open
    override willUpdate(changed: PropertyValues<this>): void {
        super.willUpdate(changed);
        if (changed.has("ringUuid") && this.manager && this.ringUuid) {
            this.manager.ringUuid = this.ringUuid;
        }
    }

    // Called by <ak-forms-modal> submit
    async send(): Promise<unknown> {
        // delegate save to manager
        await this.manager?.persist?.();
        return {};
    }

    getSuccessMessage(): string {
        // manager already shows errors; modal just needs a success toast
        return "Saved.";
    }

    renderForm(): TemplateResult {
        return html`
            <ak-crypto-keyring-manager
                .ringUuid=${this.ringUuid}
                .requireKey=${this.requireKey}
                .allowedKeyTypes=${this.allowedKeyTypes ?? []}
                hideFooter
            ></ak-crypto-keyring-manager>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-crypto-keyring-manager-form": AkCryptoKeyringManagerForm;
    }
}
