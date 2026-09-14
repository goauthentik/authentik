import { renderForm } from "./SAMLSourceImportFormForm.js";

import { aki } from "#common/api/client";
import { SentryIgnoredError } from "#common/sentry/index";

import { Form } from "#elements/forms/Form";

import { SAMLSource, SourcesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement } from "lit/decorators.js";

@customElement("ak-source-saml-import-form")
export class SAMLSourceImportForm extends Form<SAMLSource> {
    getSuccessMessage(): string {
        return msg("Successfully imported source.");
    }

    async send(data: SAMLSource): Promise<unknown> {
        const file = this.files().get("file");
        if (!file) {
            throw new SentryIgnoredError("No form data");
        }
        const api = aki(SourcesApi);
        const created: SAMLSource = await api.sourcesSamlImportMetadataCreate({
            file: file,
            name: data.name,
            preAuthenticationFlow: data.preAuthenticationFlow || "",
        });

        return api.sourcesSamlPartialUpdate({
            slug: created.slug,
            patchedSAMLSourceRequest: {
                signingKp: data.signingKp || null,
                signedAssertion: data.signedAssertion ?? true,
                signedResponse: data.signedResponse ?? false,
                authenticationFlow: data.authenticationFlow || undefined,
                enrollmentFlow: data.enrollmentFlow || undefined,
            },
        });
    }

    renderForm() {
        return renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-saml-import-form": SAMLSourceImportForm;
    }
}
