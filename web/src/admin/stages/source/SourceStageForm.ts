import { BaseStageForm } from "@goauthentik/admin/stages/BaseStageForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/SearchSelect/index";
import "@goauthentik/elements/utils/TimeDeltaHelp";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    Source,
    SourceStage,
    SourcesAllListRequest,
    SourcesApi,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-source-form")
export class SourceStageForm extends BaseStageForm<SourceStage> {
    loadInstance(pk: string): Promise<SourceStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesSourceRetrieve({
            stageUuid: pk,
        });
    }

    async send(data: SourceStage): Promise<SourceStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesSourceUpdate({
                stageUuid: this.instance.pk || "",
                sourceStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesSourceCreate({
                sourceStageRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`
            <span> ${msg("TODO.")} </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Source")} ?required=${true} name="source">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Source[]> => {
                        const args: SourcesAllListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await new SourcesApi(DEFAULT_CONFIG).sourcesAllList(args);
                        return users.results;
                    }}
                    .renderElement=${(source: Source): string => {
                        return source.name;
                    }}
                    .renderDescription=${(source: Source): TemplateResult => {
                        return html`${source.verboseName}`;
                    }}
                    .value=${(source: Source | undefined): string | undefined => {
                        return source?.pk;
                    }}
                    .selected=${(source: Source): boolean => {
                        return source.pk === this.instance?.source;
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Resume timeout")}
                ?required=${true}
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
