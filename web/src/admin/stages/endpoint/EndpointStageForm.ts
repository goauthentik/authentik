import "#components/ak-text-input";
import "#elements/forms/Radio";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/FormGroup";
import { aki } from "#common/api/client";

import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import { Connector, EndpointsApi, EndpointStage, StageModeEnum, StagesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

const connectorSource: SearchSelectSource<Connector> = {
    fetchObjects: (query) =>
        aki(EndpointsApi)
            .endpointsConnectorsList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (connector) => connector.connectorUuid ?? "",
    labelOf: (connector) => connector.name,
    describe: (connector) => connector.verboseName,
};

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
                        ${AKSearchSelect({
                            name: "connector",
                            source: connectorSource,
                            value: this.instance?.connector,
                            blankable: false,
                        })}
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
