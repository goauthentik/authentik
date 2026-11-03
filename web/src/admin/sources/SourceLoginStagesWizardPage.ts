import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#elements/EmptyState";
import { aki } from "#common/api/client";
import { parseAPIResponseError } from "#common/errors/network";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";

import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { WizardPage } from "#elements/wizard/WizardPage";

import { FlowDesignationEnum, IdentificationStage, Source, StagesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

/**
 * Offered after a source is created, since a source only shows up on the login page once an
 * identification stage selects it.
 */
@customElement("ak-source-wizard-page-login-stages")
export class SourceLoginStagesWizardPage extends WizardPage {
    static styles = [PFFormControl];

    @state()
    protected stages: IdentificationStage[] | null = null;

    protected selected: string[] = [];

    protected get source(): Source | undefined {
        // The source form step is the one right after the type selection.
        return this.host.state[this.host.steps[1]] as Source | undefined;
    }

    public override activeCallback = async () => {
        // The source already exists at this point, so there is nothing left to cancel.
        this.host.cancelable = false;
        this.host.valid = true;

        // ponytail: first 100 identification stages only, page through if anyone has more.
        const { results } = await aki(StagesApi).stagesIdentificationList({ pageSize: 100 });

        this.selected = results
            .filter((stage) =>
                stage.flowSet.some(
                    (flow) => flow.designation === FlowDesignationEnum.Authentication,
                ),
            )
            .map((stage) => stage.pk);

        this.stages = results;
    };

    public override nextCallback = async () => {
        const { source, stages } = this;

        if (!source || !stages) return true;

        const api = aki(StagesApi);

        try {
            await Promise.all(
                stages
                    .filter((stage) => this.selected.includes(stage.pk))
                    .filter((stage) => !stage.sources?.includes(source.pk))
                    .map((stage) =>
                        api.stagesIdentificationPartialUpdate({
                            stageUuid: stage.pk,
                            patchedIdentificationStageRequest: {
                                sources: [...(stage.sources ?? []), source.pk],
                            },
                        }),
                    ),
            );
        } catch (error) {
            showAPIErrorMessage(await parseAPIResponseError(error));

            return false;
        }

        return true;
    };

    protected renderStageLabel(stage: IdentificationStage): SlottedTemplateResult {
        const flows = stage.flowSet.map((flow) => flow.name).join(", ");

        return html`<div>${stage.name}</div>
            <small class="pf-c-form__helper-text">
                ${
                    flows
                        ? msg(str`Used in: ${flows}`, {
                              id: "source.wizard.login-stages.stage.flows.description",
                          })
                        : msg("Not bound to any flow", {
                              id: "source.wizard.login-stages.stage.unbound.description",
                          })
                }
            </small>`;
    }

    protected override render(): SlottedTemplateResult {
        const { stages } = this;

        if (!stages) {
            return html`<ak-empty-state loading></ak-empty-state>`;
        }

        return html`<p>
                ${msg(
                    "Add this source to an Identification stage if you want it displayed on the login page. Otherwise, you can skip this step.",
                    { id: "source.wizard.login-stages.description" },
                )}
            </p>
            ${
                stages.length
                    ? html`<ak-checkbox-group
                          name="stages"
                          .options=${stages.map((stage) => [stage.pk, this.renderStageLabel(stage)])}
                          .value=${this.selected}
                          @change=${(event: CustomEvent<string[]>) => {
                              this.selected = event.detail;
                          }}
                      ></ak-checkbox-group>`
                    : html`<p>
                          ${msg("No identification stages exist yet.", {
                              id: "source.wizard.login-stages.empty",
                          })}
                      </p>`
            }`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-wizard-page-login-stages": SourceLoginStagesWizardPage;
    }
}
