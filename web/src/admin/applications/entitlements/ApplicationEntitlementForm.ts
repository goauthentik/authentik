import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { ObjectAttributeModelForm } from "#admin/object-attributes/renderAttributes";

import { ApplicationEntitlement, CoreApi, ModelEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";

@customElement("ak-application-entitlement-form")
export class ApplicationEntitlementForm extends ObjectAttributeModelForm<
    ApplicationEntitlement,
    string
> {
    public model = ModelEnum.AuthentikCoreApplicationentitlement;

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
        return html` <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            ${this.renderObjectAttributes(this.objAttributes, this.instance)}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-entitlement-form": ApplicationEntitlementForm;
    }
}
