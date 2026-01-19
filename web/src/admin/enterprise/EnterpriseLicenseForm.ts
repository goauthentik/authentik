import "#components/ak-secret-textarea-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "#common/constants";

import { ModelForm } from "#elements/forms/ModelForm";

import { EnterpriseApi, License } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-enterprise-license-form")
export class EnterpriseLicenseForm extends ModelForm<License, string> {
    @state()
    installID?: string;

    reset(): void {
        super.reset();
        this.installID = undefined;
    }

    loadInstance(pk: string): Promise<License> {
        return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseRetrieve({
            licenseUuid: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated license.")
            : msg("Successfully created license.");
    }

    async load(): Promise<void> {
        this.installID = (
            await new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseInstallIdRetrieve()
        ).installId;
    }

    async send(data: License): Promise<License> {
        return (
            this.instance
                ? new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicensePartialUpdate({
                      licenseUuid: this.instance.licenseUuid || "",
                      patchedLicenseRequest: data,
                  })
                : new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseCreate({
                      licenseRequest: data,
                  })
        ).then((data) => {
            window.dispatchEvent(new CustomEvent(EVENT_REFRESH_ENTERPRISE));
            return data;
        });
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Install ID")}>
                <input
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    readonly
                    type="text"
                    value="${ifDefined(this.installID)}"
                />
            </ak-form-element-horizontal>
            <ak-secret-textarea-input
                name="key"
                ?revealed=${!this.instance}
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
