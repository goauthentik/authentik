import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import { EnterpriseApi, License } from "@goauthentik/api";

@customElement("ak-enterprise-license-form")
export class EnterpriseLicenseForm extends ModelForm<License, string> {
    loadInstance(pk: string): Promise<License> {
        return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseRetrieve({
            licenseUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated license.");
        } else {
            return msg("Successfully created license.");
        }
    }

    async send(data: License): Promise<License> {
        if (this.instance) {
            return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicensePartialUpdate({
                licenseUuid: this.instance.licenseUuid || "",
                patchedLicenseRequest: data,
            });
        } else {
            return new EnterpriseApi(DEFAULT_CONFIG).enterpriseLicenseCreate({
                licenseRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                name="key"
                ?writeOnly=${this.instance !== undefined}
                label=${msg("License key")}
            >
                <textarea class="pf-c-form-control"></textarea>
            </ak-form-element-horizontal>
        </form>`;
    }
}
