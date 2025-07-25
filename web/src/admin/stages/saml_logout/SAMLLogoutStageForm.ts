import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { SAMLLogoutStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-saml-logout-form")
export class SAMLLogoutStageForm extends BaseStageForm<SAMLLogoutStage> {
    loadInstance(pk: string): Promise<SAMLLogoutStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesSamlLogoutRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: SAMLLogoutStage): Promise<SAMLLogoutStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesSamlLogoutUpdate({
                stageUuid: this.instance.pk || "",
                sAMLLogoutStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesSamlLogoutCreate({
            sAMLLogoutStageRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <span
                >${msg(
                    "Logs out the user from all configured SAML providers using front-channel logout.",
                )}</span
            >
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-saml-logout-form": SAMLLogoutStageForm;
    }
}
