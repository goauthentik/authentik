import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    Flow,
    FlowsApi,
    FlowsInstancesListRequest,
    RedirectStage,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-redirect-form")
export class RedirectStageForm extends BaseStageForm<RedirectStage> {
    loadInstance(pk: string): Promise<RedirectStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesRedirectRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: RedirectStage): Promise<RedirectStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesRedirectUpdate({
                stageUuid: this.instance.pk || "",
                redirectStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesRedirectCreate({
                redirectStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<span>
                ${msg("Let the user identify themselves with their username or Email address.")}
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
                    <ak-form-element-horizontal
                        label=${msg("Redirect to Flow")}
                        name="redirectToFlow"
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
                            .renderElement=${(flow: Flow): string => {
                                return RenderFlowOption(flow);
                            }}
                            .renderDescription=${(flow: Flow): TemplateResult => {
                                return html`${flow.name}`;
                            }}
                            .value=${(flow: Flow | undefined): string | undefined => {
                                return flow?.pk;
                            }}
                            .selected=${(flow: Flow): boolean => {
                                return this.instance?.redirectToFlow === flow.pk;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "When selected, a password field is shown on the same page instead of a separate page. This prevents username enumeration attacks.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="keepContext">
                        <label class="pf-c-switch">
                            <input
                                class="pf-c-switch__input"
                                type="checkbox"
                                ?checked=${first(this.instance?.keepContext, false)}
                            />
                            <span class="pf-c-switch__toggle">
                                <span class="pf-c-switch__toggle-icon">
                                    <i class="fas fa-check" aria-hidden="true"></i>
                                </span>
                            </span>
                            <span class="pf-c-switch__label">${msg("Keep context?")}</span>
                        </label>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-redirect-form": RedirectStageForm;
    }
}
