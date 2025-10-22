import { renderForm } from "./SAMLProviderFormForm.js";
import { signatureAlgorithmOptions } from "./SAMLProviderOptions.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { type AkCryptoCertificateSearch } from "#admin/common/ak-crypto-certificate-search";
import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import {
    CryptoApi,
    ProvidersApi,
    SAMLBindingsEnum,
    SAMLProvider,
    SAMLProviderLogoutMethodEnum,
} from "@goauthentik/api";

import { customElement, state } from "lit/decorators.js";

@customElement("ak-provider-saml-form")
export class SAMLProviderFormPage extends BaseProviderForm<SAMLProvider> {
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

    async loadInstance(pk: number): Promise<SAMLProvider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersSamlRetrieve({
            id: pk,
        });
        this.hasSigningKp = !!provider.signingKp;
        this.hasSlsUrl = !!provider.slsUrl;
        this.hasPostBinding = provider.slsBinding === SAMLBindingsEnum.Post;
        this.logoutMethod =
            provider.logoutMethod ?? SAMLProviderLogoutMethodEnum.FrontchannelIframe;
        return provider;
    }

    async send(data: SAMLProvider): Promise<SAMLProvider> {
        if (data.signatureAlgorithm && this.signingKeyType) {
            const shaValue = data.signatureAlgorithm; // e.g., "sha256"
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
                data.signatureAlgorithm = matchingAlgorithm.value;
            }
        }
        // If SLS binding is redirect, ensure logout method is not backchannel
        if (
            data.slsBinding === SAMLBindingsEnum.Redirect &&
            data.logoutMethod === SAMLProviderLogoutMethodEnum.Backchannel
        ) {
            data.logoutMethod = SAMLProviderLogoutMethodEnum.FrontchannelIframe;
        }

        if (this.instance) {
            return new ProvidersApi(DEFAULT_CONFIG).providersSamlUpdate({
                id: this.instance.pk,
                sAMLProviderRequest: data,
            });
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersSamlCreate({
            sAMLProviderRequest: data,
        });
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

        return renderForm({
            provider: this.instance,
            setHasSigningKp,
            hasSigningKp: this.hasSigningKp,
            setHasSlsUrl,
            hasSlsUrl: this.hasSlsUrl,
            setSlsBinding,
            hasPostBinding: this.hasPostBinding,
            logoutMethod: this.logoutMethod,
            setLogoutMethod,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-form": SAMLProviderFormPage;
    }
}
