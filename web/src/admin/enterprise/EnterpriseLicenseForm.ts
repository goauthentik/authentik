import "#components/ak-secret-textarea-input";
import "#components/ak-text-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";
import { EVENT_REFRESH_ENTERPRISE } from "#common/constants";

import { AKElement } from "#elements/Base";
import { formatCreateLabel } from "#elements/dialogs/shared";
import { ModelForm } from "#elements/forms/ModelForm";
import { toAdminInterface } from "#elements/router/core/interfaces";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { EnterpriseApi, License } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

import "#components/ak-full-page-form";

import { customElement, state } from "lit/decorators.js";

@customElement("ak-enterprise-license-form")
export class EnterpriseLicenseForm extends ModelForm<License, string> {
    public static override verboseName = msg("Enterprise License");
    public static override verboseNamePlural = msg("Enterprise Licenses");
    public static override createLabel = msg("Install");
    public static override submitVerb = msg("Install");

    #api = aki(EnterpriseApi);

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

/**
 * The enterprise license form as a full page, for the `/enterprise/licenses/new` route.
 */
@customElement("ak-enterprise-license-form-page")
export class EnterpriseLicenseFormPage extends AKElement {
    protected override render() {
        return html`<ak-full-page-form
            header=${formatCreateLabel(EnterpriseLicenseForm)}
            icon="pf-icon pf-icon-key"
            return-url=${toAdminInterface("enterprise/licenses")}
        >
            <ak-enterprise-license-form></ak-enterprise-license-form>
        </ak-full-page-form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-enterprise-license-form": EnterpriseLicenseForm;
        "ak-enterprise-license-form-page": EnterpriseLicenseFormPage;
    }
}
