import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";



import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";



import { MutualTLSStage, StagesApi } from "@goauthentik/api";





@customElement("ak-stage-mtls-form")
export class MTLSStageForm extends BaseStageForm<MutualTLSStage> {
    loadInstance(pk: string): Promise<MutualTLSStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesMtlsRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: MutualTLSStage): Promise<MutualTLSStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesMtlsUpdate({
                stageUuid: this.instance.pk || "",
                mutualTLSStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesMtlsCreate({
                mutualTLSStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Dummy stage used for testing. Shows a simple continue button and always passes.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="throwError">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${this.instance?.throwError ?? false}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Throw error?")}</span>
                </label>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-mtls-form": MutualTLSStageForm;
    }
}
