import "#elements/forms/Radio";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#elements/forms/FormGroup";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    Connector,
    EndpointsApi,
    EndpointsConnectorsListRequest,
    EndpointStage,
    StageModeEnum,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-endpoints-stage-form")
export class EndpointStageForm extends BaseStageForm<EndpointStage> {
    loadInstance(pk: string): Promise<EndpointStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesEndpointsRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: EndpointStage): Promise<EndpointStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesEndpointsUpdate({
                stageUuid: this.instance.pk || "",
                endpointStageRequest: data,
            });
        }
        return new StagesApi(DEFAULT_CONFIG).stagesEndpointsCreate({
            endpointStageRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg("Stage which associates the currently used device with the current session.")}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group open label="${msg("Stage-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Connector")} required name="connector">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Connector[]> => {
                                const args: EndpointsConnectorsListRequest = {
                                    ordering: "name",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const users = await new EndpointsApi(
                                    DEFAULT_CONFIG,
                                ).endpointsConnectorsList(args);
                                return users.results;
                            }}
                            .renderElement=${(connector: Connector): string => {
                                return connector.name;
                            }}
                            .renderDescription=${(connector: Connector): TemplateResult => {
                                return html`${connector.verboseName}`;
                            }}
                            .value=${(connector: Connector | undefined): string | undefined => {
                                return connector?.connectorUuid;
                            }}
                            .selected=${(connector: Connector): boolean => {
                                return connector.connectorUuid === this.instance?.connector;
                            }}
                        >
                        </ak-search-select>
                    </ak-form-element-horizontal>

                    <ak-form-element-horizontal label=${msg("Mode")} required name="mode">
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Device optional"),
                                    value: StageModeEnum.Optional,
                                    default: true,
                                    description: html`${msg(
                                        "If no device was provided, this stage will succeed and continue to the next stage.",
                                    )}`,
                                },
                                {
                                    label: msg("Device required"),
                                    value: StageModeEnum.Required,
                                    description: html`${msg(
                                        "If no device was provided, this stage will stop flow execution.",
                                    )}`,
                                },
                            ]}
                            .value=${this.instance?.mode}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-endpoints-stage-form": EndpointStageForm;
    }
}
