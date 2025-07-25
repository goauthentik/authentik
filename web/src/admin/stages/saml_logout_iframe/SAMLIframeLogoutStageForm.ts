import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { SAMLIframeLogoutStage, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-stage-saml-iframe-logout-form")
export class SAMLIframeLogoutStageForm extends BaseStageForm<SAMLIframeLogoutStage> {
    loadInstance(pk: string): Promise<SAMLIframeLogoutStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesSamlLogoutIframeRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: SAMLIframeLogoutStage): Promise<SAMLIframeLogoutStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesSamlLogoutIframePartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedSAMLIframeLogoutStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesSamlLogoutIframeCreate({
            sAMLIframeLogoutStageRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <span
                >${msg(
                    "Handles SAML logout for providers that don't support redirect-based logout by using hidden iframes.",
                )}</span
            >
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Iframe timeout")}
                required
                name="iframeTimeout"
            >
                <input
                    type="number"
                    value="${ifDefined(this.instance?.iframeTimeout || 5000)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Timeout in milliseconds to wait for each iframe to load before considering it failed.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-saml-iframe-logout-form": SAMLIframeLogoutStageForm;
    }
}
