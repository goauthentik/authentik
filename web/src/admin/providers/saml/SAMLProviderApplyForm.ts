import { renderForm } from "./SAMLProviderApplyFormForm.js";

import { aki } from "#common/api/client";
import { SentryIgnoredError } from "#common/sentry/index";

import { Form } from "#elements/forms/Form";

import { ProvidersApi, SAMLProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-provider-saml-apply-metadata-form")
export class SAMLProviderApplyMetadataForm extends Form<SAMLProvider> {
    @property({ type: Number }) providerId?: number;

    @property({ type: String }) providerName = "";

    getSuccessMessage(): string {
        return msg("Successfully applied metadata.");
    }

    async send(_data: SAMLProvider): Promise<unknown> {
        if (!this.providerId) throw new SentryIgnoredError("No providerId");

        const formEl = this.shadowRoot?.querySelector("form");
        const fileInput = formEl?.querySelector(
            'input[type="file"][name="file"]',
        ) as HTMLInputElement | null;

        const file = fileInput?.files?.item(0) ?? null;
        if (!file) throw new SentryIgnoredError("No form data");

        const signingCertificate =
            (formEl?.querySelector('[name="signingCertificate"]') as HTMLInputElement | null)
                ?.value ?? undefined;

        const payload: Parameters<ProvidersApi["providersSamlImportMetadataCreate"]>[0] = {
            provider: this.providerId,
            name: this.providerName,
            file,
            createMissingRings: true,
        };
        if (signingCertificate && signingCertificate.trim() !== "") {
            payload.signingCertificate = signingCertificate.trim();
        }
        return aki(ProvidersApi).providersSamlImportMetadataCreate(payload);
    }

    renderForm() {
        return renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-apply-metadata-form": SAMLProviderApplyMetadataForm;
    }
}
