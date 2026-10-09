import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/utils/TimeDeltaHelp";
import { aki } from "#common/api/client";

import { SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import {
    ResumeOnMatchFailuresEnum,
    Source,
    SourcesApi,
    SourceStage,
    StagesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const sourceSource: SearchSelectSource<Source> = {
    fetchObjects: (query) =>
        aki(SourcesApi)
            .sourcesAllList(withQuery(query, { ordering: "name" }))
            .then(({ results }) => results),
    keyOf: (source) => source.pk,
    labelOf: (source) => source.name,
    describe: (source) => source.verboseName,
};

@customElement("ak-stage-source-form")
export class SourceStageForm extends BaseStageForm<SourceStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesSourceRetrieve({ stageUuid }),
        create: (sourceStageRequest: SourceStage) =>
            aki(StagesApi).stagesSourceCreate({ sourceStageRequest }),
        update: (stageUuid: string, sourceStageRequest: SourceStage) =>
            aki(StagesApi).stagesSourceUpdate({ stageUuid, sourceStageRequest }),
    };

    protected override renderForm(): TemplateResult {
        return html`
            <span
                >${msg(
                    "Inject an OAuth or SAML Source into the flow execution. This allows for additional user verification, or to dynamically access different sources for different user identifiers (username, email address, etc).",
                )}</span
            >
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
            <ak-form-element-horizontal label=${msg("Source")} required name="source">
                ${AKSearchSelect({
                    name: "source",
                    source: sourceSource,
                    value: this.instance?.source,
                    blankable: false,
                })}
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Resume on matching failures", {
                    id: "stages.source.resume-on-match-failures.label",
                })}
                name="resumeOnMatchFailures"
            >
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Resume this flow for the selected source matching failures. No source connection is created.",
                        {
                            id: "stages.source.resume-on-match-failures.description",
                        },
                    )}
                </p>
                <ak-checkbox-group
                    .options=${[
                        {
                            name: ResumeOnMatchFailuresEnum.MissingProperty,
                            label: msg("Missing property", {
                                id: "stages.source.match-failure.missing-property.label",
                            }),
                        },
                    ]}
                    .value=${this.instance?.resumeOnMatchFailures ?? []}
                ></ak-checkbox-group>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Resume timeout")}
                required
                name="resumeTimeout"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.resumeTimeout || "minutes=10")}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Amount of time a user can take to return from the source to continue the flow.",
                    )}
                </p>
                <ak-utils-time-delta-help></ak-utils-time-delta-help>
            </ak-form-element-horizontal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-source-form": SourceStageForm;
    }
}
