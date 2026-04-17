import "#components/ak-secret-textarea-input";
import "#components/ak-text-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "#common/constants";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { EnterpriseApi, License } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-enterprise-license-form")
export class EnterpriseLicenseForm extends ModelForm<License, string> {
    public static override verboseName = msg("Enterprise License");
    public static override verboseNamePlural = msg("Enterprise Licenses");
    public static override createLabel = msg("Install");
    public static override submitVerb = msg("Install");

    #api = new EnterpriseApi(DEFAULT_CONFIG);

    @state()
    protected installID: string | null = null;

    public override reset(): void {
        super.reset();

        this.installID = null;
    }

    loadInstance(pk: string): Promise<License> {
        return this.#api.enterpriseLicenseRetrieve({
            licenseUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated license.")
            : msg("Successfully created license.");
    }

    async load(): Promise<void> {
        this.installID = (await this.#api.enterpriseLicenseInstallIdRetrieve()).installId;
    }

    async send(data: License): Promise<License> {
        return (
            this.instance
                ? this.#api.enterpriseLicensePartialUpdate({
                      licenseUuid: this.instance.licenseUuid || "",
                      patchedLicenseRequest: data,
                  })
                : this.#api.enterpriseLicenseCreate({
                      licenseRequest: data,
                  })
        ).then((data) => {
            window.dispatchEvent(new CustomEvent(EVENT_REFRESH_ENTERPRISE));
            return data;
        });
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                label=${msg("Install ID")}
                autocomplete="off"
                spellcheck="false"
                readonly
                type="text"
                name="installID"
                input-hint="code"
                value="${ifPresent(this.installID)}"
            >
            </ak-text-input>
            <ak-secret-textarea-input
                name="key"
                ?required=${!this.instance}
                ?revealed=${!this.instance}
                placeholder=${msg("Paste your license key...")}
                label=${msg("License key")}
                input-hint="code"
            >
            </ak-secret-textarea-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enterprise-license-form": EnterpriseLicenseForm;
    }
}
