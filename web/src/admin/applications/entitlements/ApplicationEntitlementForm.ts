import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";

import { ApplicationEntitlement, CoreApi } from "@goauthentik/api";

@customElement("ak-application-entitlement-form")
export class ApplicationEntitlementForm extends ModelForm<ApplicationEntitlement, string> {
    async loadInstance(pk: string): Promise<ApplicationEntitlement> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsRetrieve({
            pbmUuid: pk,
        });
    }

    @property()
    targetPk?: string;

    getSuccessMessage(): string {
        if (this.instance?.pbmUuid) {
            return msg("Successfully updated entitlement.");
        } else {
            return msg("Successfully created entitlement.");
        }
    }

    static get styles(): CSSResult[] {
        return [...super.styles, PFContent];
    }

    send(data: ApplicationEntitlement): Promise<unknown> {
        if (this.targetPk) {
            data.app = this.targetPk;
        }
        if (this.instance?.pbmUuid) {
            return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsUpdate({
                pbmUuid: this.instance.pbmUuid || "",
                applicationEntitlementRequest: data,
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsCreate({
                applicationEntitlementRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Attributes")}
                ?required=${false}
                name="attributes"
            >
                <ak-codemirror
                    mode=${CodeMirrorMode.YAML}
                    value="${YAML.stringify(first(this.instance?.attributes, {}))}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-entitlement-form": ApplicationEntitlementForm;
    }
}
