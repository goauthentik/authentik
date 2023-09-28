import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { DenyStage, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-deny-form")
export class DenyStageForm extends ModelForm<DenyStage, string> {
    loadInstance(pk: string): Promise<DenyStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesDenyRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
        }
    }

    async send(data: DenyStage): Promise<DenyStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesDenyUpdate({
                stageUuid: this.instance.pk || "",
                denyStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesDenyCreate({
                denyStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <span>
                ${msg(
                    "Statically deny the flow. To use this stage effectively, disable *Evaluate when flow is planned* on the respective binding.",
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
        </form>`;
    }
}
