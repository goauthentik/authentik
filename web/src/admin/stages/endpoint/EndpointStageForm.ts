import "#components/ak-text-input";
import "#elements/forms/Radio";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#elements/forms/FormGroup";

import { aki } from "#common/api/client";

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

@customElement("ak-endpoints-stage-form")
export class EndpointStageForm extends BaseStageForm<EndpointStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesEndpointsRetrieve({ stageUuid }),
        create: (endpointStageRequest: EndpointStage) =>
            aki(StagesApi).stagesEndpointsCreate({ endpointStageRequest }),
        update: (stageUuid: string, endpointStageRequest: EndpointStage) =>
            aki(StagesApi).stagesEndpointsUpdate({ stageUuid, endpointStageRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg("Stage which associates the currently used device with the current session.")}
            </span>
            <ak-text-input
                label=${msg("Stage Name", {
                    id: "stage.name.label",
                })}
                required
                name="name"
                value=${this.instance?.name || ""}
                placeholder=${msg("Type a name for this stage...", {
                    id: "stage.name.placeholder",
                })}
                ?autofocus=${!this.instance}
            ></ak-text-input>
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
                                const users = await aki(EndpointsApi).endpointsConnectorsList(args);
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
