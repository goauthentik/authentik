import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import {
    Flow,
    FlowsApi,
    FlowsInstancesListRequest,
    RedirectStage,
    RedirectStageModeEnum,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-redirect-form")
export class RedirectStageForm extends BaseStageForm<RedirectStage> {
    @property({ type: String })
    mode: string = RedirectStageModeEnum.Static;

    loadInstance(pk: string): Promise<RedirectStage> {
        return new StagesApi(DEFAULT_CONFIG)
            .stagesRedirectRetrieve({
                stageUuid: pk,
            })
            .then((stage) => {
                this.mode = stage.mode ?? RedirectStageModeEnum.Static;
                return stage;
            });
    }

    async send(data: RedirectStage): Promise<RedirectStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesRedirectUpdate({
                stageUuid: this.instance.pk || "",
                redirectStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesRedirectCreate({
            redirectStageRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`<span>
                ${msg("Redirect the user to another flow, potentially with all gathered context")}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${this.instance?.name ?? ""}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group expanded>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Mode")} required name="mode">
                        <select
                            class="pf-c-form-control"
                            @change=${(ev: Event) => {
                                const target = ev.target as HTMLSelectElement;
                                this.mode = target.selectedOptions[0].value;
                            }}
                        >
                            <option
                                value=${RedirectStageModeEnum.Static}
                                ?selected=${this.instance?.mode === RedirectStageModeEnum.Static}
                            >
                                ${msg("Static")}
                            </option>
                            <option
                                value=${RedirectStageModeEnum.Flow}
                                ?selected=${this.instance?.mode === RedirectStageModeEnum.Flow}
                            >
                                ${msg("Flow")}
                            </option>
                        </select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        ?hidden=${this.mode !== RedirectStageModeEnum.Static}
                        label=${msg("Target URL")}
                        name="targetStatic"
                        required
                    >
                        <input
                            type="text"
                            value="${this.instance?.targetStatic ?? ""}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Redirect the user to a static URL.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        ?hidden=${this.mode !== RedirectStageModeEnum.Flow}
                        label=${msg("Target Flow")}
                        name="targetFlow"
                        required
                    >
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(
                                    args,
                                );
                                return flows.results;
                            }}
                            .renderElement=${(flow: Flow): string => RenderFlowOption(flow)}
                            .renderDescription=${(flow: Flow): TemplateResult => html`${flow.name}`}
                            .value=${(flow: Flow | undefined): string | undefined => flow?.pk}
                            .selected=${(flow: Flow): boolean =>
                                this.instance?.targetFlow === flow.pk}
                            blankable
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">${msg("Redirect the user to a Flow.")}</p>
                    </ak-form-element-horizontal>
                    <ak-switch-input
                        ?hidden=${this.mode !== RedirectStageModeEnum.Flow}
                        name="keepContext"
                        label=${msg("Keep flow context")}
                        ?checked="${this.instance?.keepContext ?? true}"
                    >
                    </ak-switch-input>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-redirect-form": RedirectStageForm;
    }
}
