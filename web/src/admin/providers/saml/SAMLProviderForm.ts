import { renderForm } from "./SAMLProviderFormForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { type AkCryptoCertificateSearch } from "#admin/common/ak-crypto-certificate-search";
import { BaseProviderForm } from "#admin/providers/BaseProviderForm";

import {
    KeyTypeEnum,
    ProvidersApi,
    SAMLBindingsEnum,
    SAMLLogoutMethods,
    SAMLProvider,
} from "@goauthentik/api";

import { customElement, state } from "lit/decorators.js";

@customElement("ak-provider-saml-form")
export class SAMLProviderFormPage extends BaseProviderForm<SAMLProvider> {
    @state()
    protected hasSigningKp = false;

    @state()
    protected verificationKeyMode: "kp" | "ring" = "kp";

    @state()
    protected encryptionKeyMode: "kp" | "ring" = "kp";

    @state()
    protected signingKeyMode: "kp" | "ring" = "kp";

    @state()
    protected hasSlsUrl = false;

    @state()
    protected hasPostBinding = false;

    @state()
    protected logoutMethod: SAMLLogoutMethods = SAMLLogoutMethods.FrontchannelIframe;

    public override reset(): void {
        super.reset();

        this.hasSigningKp = false;
        this.hasSlsUrl = false;
        this.hasPostBinding = false;
        this.logoutMethod = SAMLLogoutMethods.FrontchannelIframe;
    }

    @state()
    protected signingKeyType: KeyTypeEnum | null = null;

    async loadInstance(pk: number): Promise<SAMLProvider> {
        const provider = await new ProvidersApi(DEFAULT_CONFIG).providersSamlRetrieve({
            id: pk,
        });
        this.hasSigningKp = !!provider.signingKp;
        this.hasSlsUrl = !!provider.slsUrl;
        this.hasPostBinding = provider.slsBinding === SAMLBindingsEnum.Post;
        this.logoutMethod = provider.logoutMethod ?? SAMLLogoutMethods.FrontchannelIframe;

        this.signingKeyMode = provider.signingKp ? "kp" : provider.signingKpRing ? "ring" : "kp";
        this.verificationKeyMode = provider.verificationKp
            ? "kp"
            : provider.verificationKpRing
              ? "ring"
              : "kp";
        this.encryptionKeyMode = provider.encryptionKp
            ? "kp"
            : provider.encryptionKpRing
              ? "ring"
              : "kp";

        return provider;
    }

    async send(data: SAMLProvider): Promise<SAMLProvider> {
        // If SLS binding is redirect, ensure logout method is not backchannel
        if (
            data.slsBinding === SAMLBindingsEnum.Redirect &&
            data.logoutMethod === SAMLLogoutMethods.Backchannel
        ) {
            data.logoutMethod = SAMLLogoutMethods.FrontchannelIframe;
        }

        if (this.signingKeyMode === "kp") {
            data.signingKpRing = null;
        } else {
            data.signingKp = null;
        }

        if (this.verificationKeyMode === "kp") {
            data.verificationKpRing = null;
        } else {
            data.verificationKp = null;
        }

        if (this.encryptionKeyMode === "kp") {
            data.encryptionKpRing = null;
        } else {
            data.encryptionKp = null;
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
        const setHasSigningKp = (ev: InputEvent) => {
            const target = ev.target as AkCryptoCertificateSearch;
            if (!target) return;
            this.hasSigningKp = !!target.selectedKeypair;
            this.signingKeyType = target.selectedKeypair?.keyType ?? KeyTypeEnum.Rsa;
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
                this.logoutMethod === SAMLLogoutMethods.Backchannel
            ) {
                this.logoutMethod = SAMLLogoutMethods.FrontchannelIframe;
            }
        };

        const setLogoutMethod = (ev: Event) => {
            const target = ev.target as HTMLInputElement;
            this.logoutMethod = target.value as SAMLLogoutMethods;
        };

        const setSigningKeyMode = (ev: Event) => {
            const target = ev.target as HTMLInputElement;
            this.signingKeyMode = target.value as "kp" | "ring";
            this.hasSigningKp = this.signingKeyMode === "kp" && !!this.instance?.signingKp;
        };

        const setVerificationKeyMode = (ev: Event) => {
            const target = ev.target as HTMLInputElement;
            this.verificationKeyMode = target.value as "kp" | "ring";
        };

        const setEncryptionKeyMode = (ev: Event) => {
            const target = ev.target as HTMLInputElement;
            this.encryptionKeyMode = target.value as "kp" | "ring";
        };
        return renderForm({
            provider: this.instance,
            setHasSigningKp,
            hasSigningKp: this.hasSigningKp,
            signingKeyType: this.signingKeyType,
            setHasSlsUrl,
            hasSlsUrl: this.hasSlsUrl,
            setSlsBinding,
            hasPostBinding: this.hasPostBinding,
            logoutMethod: this.logoutMethod,
            setLogoutMethod,

            signingKeyMode: this.signingKeyMode,
            setSigningKeyMode,
            verificationKeyMode: this.verificationKeyMode,
            setVerificationKeyMode,
            encryptionKeyMode: this.encryptionKeyMode,
            setEncryptionKeyMode,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-form": SAMLProviderFormPage;
    }
}
