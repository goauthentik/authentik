import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { ConsentStage, ConsentStageModeEnum, StagesApi } from "@goauthentik/api";

@customElement("ak-stage-consent-form")
export class ConsentStageForm extends ModelForm<ConsentStage, string> {
    loadInstance(pk: string): Promise<ConsentStage> {
        return new StagesApi(DEFAULT_CONFIG)
            .stagesConsentRetrieve({
                stageUuid: pk,
            })
            .then((stage) => {
                this.showExpiresIn = stage.mode === ConsentStageModeEnum.Expiring;
                return stage;
            });
    }

    @property({ type: Boolean })
    showExpiresIn = false;

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
        }
    }

    async send(data: ConsentStage): Promise<ConsentStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesConsentUpdate({
                stageUuid: this.instance.pk || "",
                consentStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesConsentCreate({
                consentStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <span>
                ${msg(
                    "Prompt for the user's consent. The consent can either be permanent or expire in a defined amount of time.",
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
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Mode")} ?required=${true} name="mode">
                        <select
                            class="pf-c-form-control"
                            @change=${(ev: Event) => {
                                const target = ev.target as HTMLSelectElement;
                                if (
                                    target.selectedOptions[0].value ===
                                    ConsentStageModeEnum.Expiring
                                ) {
                                    this.showExpiresIn = true;
                                } else {
                                    this.showExpiresIn = false;
                                }
                            }}
                        >
                            <option
                                value=${ConsentStageModeEnum.AlwaysRequire}
                                ?selected=${this.instance?.mode ===
                                ConsentStageModeEnum.AlwaysRequire}
                            >
                                ${msg("Always require consent")}
                            </option>
                            <option
                                value=${ConsentStageModeEnum.Permanent}
                                ?selected=${this.instance?.mode === ConsentStageModeEnum.Permanent}
                            >
                                ${msg("Consent given last indefinitely")}
                            </option>
                            <option
                                value=${ConsentStageModeEnum.Expiring}
                                ?selected=${this.instance?.mode === ConsentStageModeEnum.Expiring}
                            >
                                ${msg("Consent expires.")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        ?hidden=${!this.showExpiresIn}
                        label=${msg("Consent expires in")}
                        ?required=${true}
                        name="consentExpireIn"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.consentExpireIn || "weeks=4")}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Offset after which consent expires.")}
                        </p>
                        <ak-utils-time-delta-help></ak-utils-time-delta-help>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
