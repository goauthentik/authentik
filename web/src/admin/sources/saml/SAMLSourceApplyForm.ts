import { renderForm } from "./SAMLSourceApplyFormForm.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { SentryIgnoredError } from "#common/sentry/index";

import { Form } from "#elements/forms/Form";

import { SourcesApi, SAMLSource } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-saml-apply-metadata-form")
export class SAMLSourceApplyMetadataForm extends Form<SAMLSource> {
    @property({ type: String }) sourceId = "";

    @property({ type: String }) sourceName = "";

    getSuccessMessage(): string {
        return msg("Successfully applied metadata.");
    }

    async send(_data: SAMLSource): Promise<unknown> {
        if (!this.sourceId) throw new SentryIgnoredError("No sourceId");

        const formEl = this.shadowRoot?.querySelector("form");
        const fileInput = formEl?.querySelector(
            'input[type="file"][name="file"]',
        ) as HTMLInputElement | null;

        const file = fileInput?.files?.item(0) ?? null;
        if (!file) throw new SentryIgnoredError("No form data");

        const signingCertificate =
            (formEl?.querySelector('[name="signingCertificate"]') as HTMLInputElement | null)
                ?.value ?? undefined;

        const payload: Parameters<SourcesApi["sourcesSamlImportMetadataCreate"]>[0] = {
            source: this.sourceId,
            name: this.sourceName,
            file,
            createMissingRings: true,
        };
        if (signingCertificate && signingCertificate.trim() !== "") {
            payload.signingCertificate = signingCertificate.trim();
        }
        return new SourcesApi(DEFAULT_CONFIG).sourcesSamlImportMetadataCreate(payload);
    }

    renderForm() {
        return renderForm();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-saml-apply-metadata-form": SAMLSourceApplyMetadataForm;
    }
}
