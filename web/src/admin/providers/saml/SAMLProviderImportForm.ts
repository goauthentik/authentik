import { renderForm } from "./SAMLProviderImportFormForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { SentryIgnoredError } from "#common/sentry/index";

import { Form } from "#elements/forms/Form";

import { ProvidersApi, SAMLProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

@customElement("ak-provider-saml-import-form")
export class SAMLProviderImportForm extends Form<SAMLProvider> {
    getSuccessMessage(): string {
        return msg("Successfully imported provider.");
    }

    async send(data: SAMLProvider): Promise<unknown> {
        const file = this.files().get("file");
        if (!file) {
            throw new SentryIgnoredError("No form data");
        }
        return new ProvidersApi(DEFAULT_CONFIG).providersSamlImportMetadataCreate({
            file: file,
            name: data.name,
            authorizationFlow: data.authorizationFlow || "",
            invalidationFlow: data.invalidationFlow || "",
        });
    }

    renderForm() {
        return renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-saml-import-form": SAMLProviderImportForm;
    }
}
