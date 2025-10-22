import "#admin/applications/wizard/ak-wizard-title";
import "#elements/forms/FormGroup";

import { ApplicationWizardProviderForm } from "./ApplicationWizardProviderForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { type AkCryptoCertificateSearch } from "#admin/common/ak-crypto-certificate-search";
import { renderForm } from "#admin/providers/saml/SAMLProviderFormForm";
import { signatureAlgorithmOptions } from "#admin/providers/saml/SAMLProviderOptions";

import {
    CryptoApi,
    SAMLBindingsEnum,
    SAMLProvider,
    SAMLProviderLogoutMethodEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, state } from "@lit/reactive-element/decorators.js";
import { html } from "lit";

@customElement("ak-application-wizard-provider-for-saml")
export class ApplicationWizardProviderSamlForm extends ApplicationWizardProviderForm<SAMLProvider> {
    label = msg("Configure SAML Provider");

    @state()
    protected hasSigningKp = false;

    @state()
    protected hasSlsUrl = false;

    @state()
    protected hasPostBinding = false;

    @state()
    protected logoutMethod: string = SAMLProviderLogoutMethodEnum.FrontchannelIframe;

    @state()
    protected signingKeyType: string | null = null;

    get formValues() {
        const values = super.formValues;

        // Transform signatureAlgorithm from "sha256" to full enum value
        if (values.signatureAlgorithm && this.signingKeyType) {
            const shaValue = values.signatureAlgorithm; // e.g., "sha256"
            const keyType = this.signingKeyType.toLowerCase(); // e.g., "rsa", "ec", "dsa"

            // Map key type to the format used in enum
            const keyTypeMap: Record<string, string> = {
                rsa: "rsa",
                ec: "ecdsa",
                dsa: "dsa",
            };

            const mappedKeyType = keyTypeMap[keyType] || keyType;
            const algorithmKey = `${mappedKeyType}-${shaValue}`;

            // Find the matching enum value
            const matchingAlgorithm = signatureAlgorithmOptions.find(
                (opt) => opt.label.toLowerCase() === algorithmKey,
            );

            if (matchingAlgorithm) {
                values.signatureAlgorithm = matchingAlgorithm.value;
            }
        }

        // If SLS binding is redirect, ensure logout method is not backchannel
        if (
            values.slsBinding === SAMLBindingsEnum.Redirect &&
            values.logoutMethod === SAMLProviderLogoutMethodEnum.Backchannel
        ) {
            return {
                ...values,
                logoutMethod: SAMLProviderLogoutMethodEnum.FrontchannelIframe,
            };
        }
        return values;
    }

    renderForm() {
        const setHasSigningKp = async (ev: InputEvent) => {
            const target = ev.target as AkCryptoCertificateSearch;
            if (!target) return;
            this.hasSigningKp = !!target.selectedKeypair;

            // Fetch full certificate details to get the privateKeyType
            if (target.selectedKeypair?.pk) {
                try {
                    const fullCert = await new CryptoApi(
                        DEFAULT_CONFIG,
                    ).cryptoCertificatekeypairsRetrieve({
                        kpUuid: target.selectedKeypair.pk,
                    });
                    this.signingKeyType = fullCert.privateKeyType;
                } catch (error) {
                    console.error("Failed to fetch certificate details", error);
                    this.signingKeyType = null;
                }
            } else {
                this.signingKeyType = null;
            }
        };

        const setHasSlsUrl = (ev: Event) => {
            const akTextInput = ev.currentTarget as HTMLElement & { value?: string };
            if (!akTextInput) return;

            const value = akTextInput.value || "";
            this.hasSlsUrl = !!value;
        };

        const setSlsBinding = (ev: Event) => {
            const target = ev.target as HTMLInputElement;
            this.hasPostBinding = target.value === SAMLBindingsEnum.Post;

            // If switching to redirect binding, change logout method from backchannel if needed
            if (
                target.value === SAMLBindingsEnum.Redirect &&
                this.logoutMethod === SAMLProviderLogoutMethodEnum.Backchannel
            ) {
                this.logoutMethod = SAMLProviderLogoutMethodEnum.FrontchannelIframe;
            }
        };

        const setLogoutMethod = (ev: Event) => {
            const target = ev.target as HTMLInputElement;
            this.logoutMethod = target.value;
        };

        return html` <ak-wizard-title>${this.label}</ak-wizard-title>
            <form id="providerform" class="pf-c-form pf-m-horizontal" slot="form">
                ${renderForm({
                    provider: this.wizard.provider as SAMLProvider,
                    errors: this.wizard.errors?.provider,
                    setHasSigningKp,
                    hasSigningKp: this.hasSigningKp,
                    setHasSlsUrl,
                    hasSlsUrl: this.hasSlsUrl,
                    setSlsBinding,
                    hasPostBinding: this.hasPostBinding,
                    logoutMethod: this.logoutMethod,
                    setLogoutMethod,
                })}
            </form>`;
    }

    render() {
        if (!(this.wizard.provider && this.wizard.errors)) {
            throw new Error("SAML Provider Step received uninitialized wizard context.");
        }
        return this.renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-wizard-provider-for-saml": ApplicationWizardProviderSamlForm;
    }
}
