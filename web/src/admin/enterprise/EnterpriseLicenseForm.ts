import "#components/ak-secret-textarea-input";
import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_REFRESH_ENTERPRISE } from "#common/constants";

import { ModelForm } from "#elements/forms/ModelForm";
import { ifPresent } from "#elements/utils/attributes";

import { EnterpriseApi, License } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-enterprise-license-form")
export class EnterpriseLicenseForm extends ModelForm<License, string> {
    @state()
    protected installID: string | null = null;

    public override reset(): void {
        super.reset();

        this.installID = null;
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

    protected override renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Install ID")}>
                <input
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    readonly
                    type="text"
                    value="${ifPresent(this.installID)}"
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
