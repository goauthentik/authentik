import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

import { ApplicationEntitlement, CoreApi } from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";

@customElement("ak-application-entitlement-form")
export class ApplicationEntitlementForm extends ModelForm<ApplicationEntitlement, string> {
    async loadInstance(pk: string): Promise<ApplicationEntitlement> {
        return aki(CoreApi).coreApplicationEntitlementsRetrieve({
            pbmUuid: pk,
        });
    }

    @property()
    targetPk?: string;

    getSuccessMessage(): string {
        if (this.instance?.pbmUuid) {
            return msg("Successfully updated entitlement.");
        }
        return msg("Successfully created entitlement.");
    }

    static styles: CSSResult[] = [...super.styles, PFContent];

    send(data: ApplicationEntitlement): Promise<unknown> {
        if (this.targetPk) {
            data.app = this.targetPk;
        }
        if (this.instance?.pbmUuid) {
            return aki(CoreApi).coreApplicationEntitlementsUpdate({
                pbmUuid: this.instance.pbmUuid || "",
                applicationEntitlementRequest: data,
            });
        }
        return aki(CoreApi).coreApplicationEntitlementsCreate({
            applicationEntitlementRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal required name="name">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "name",
                        required: true,
                    },
                    msg("Name"),
                )}
                <input
                    id="name"
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="attributes">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "attributes",
                    },
                    msg("Attributes"),
                )}
                <ak-codemirror
                    id="attributes"
                    mode="yaml"
                    value="${YAML.stringify(this.instance?.attributes ?? {})}"
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
