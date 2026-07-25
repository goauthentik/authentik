import "#admin/stages/prompt/PromptForm";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/ak-sortable-list/ak-sortable-list";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/ModalForm";
import "#elements/forms/SearchSelect/index";
import "#flow/stages/prompt/PromptStage";

import { policiesProvider, policiesSelector, resolvePrompts } from "./PromptStageFormHelpers.js";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";
import { parseAPIResponseError } from "#common/errors/network";

import { SlottedTemplateResult } from "#elements/types";

import { AKFormErrors, ErrorProp } from "#components/ak-field-errors";

import { BaseStageForm } from "#admin/stages/BaseStageForm";

import type { StageHost } from "#flow/types";

import { Prompt, PromptChallenge, PromptStage, StagesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { repeat } from "lit/directives/repeat.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDataList from "@patternfly/patternfly/components/DataList/data-list.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

/**
 * Captures the submitted preview payload instead of advancing a flow.
 */
class PreviewStageHost implements StageHost {
    challenge = undefined;
    flowSlug = undefined;
    loading = false;
    brand = undefined;
    async submit(payload: unknown): Promise<boolean> {
        this.form.previewResult = payload;
        return false;
    }

    constructor(private form: PromptStageForm) {}
}

@customElement("ak-stage-prompt-form")
export class PromptStageForm extends BaseStageForm<PromptStage> {
    protected endpoints = {
        load: (stageUuid: string) => aki(StagesApi).stagesPromptStagesRetrieve({ stageUuid }),
        create: (promptStageRequest: PromptStage) =>
            aki(StagesApi).stagesPromptStagesCreate({ promptStageRequest }),
        update: (stageUuid: string, promptStageRequest: PromptStage) =>
            aki(StagesApi).stagesPromptStagesUpdate({ stageUuid, promptStageRequest }),
    };

    /** The stage's fields, in their per-stage order. Source of truth for submission. */
    @state()
    protected selectedFields: Prompt[] = [];

    @state()
    protected preview: PromptChallenge | null = null;

    @state()
    protected previewError: ErrorProp | null = null;

    public previewResult: unknown;

    static styles: CSSResult[] = [
        ...super.styles,
        PFGrid,
        PFTitle,
        PFButton,
        PFDataList,
        css`
            .field-row {
                display: flex;
                align-items: center;
                gap: var(--pf-global--spacer--sm);
                padding: var(--pf-global--spacer--sm);
                border-bottom: 1px solid var(--pf-global--BorderColor--100);
            }
            .field-row .handle {
                cursor: grab;
                color: var(--pf-global--Color--200);
            }
            .field-row .field-info {
                flex: 1 1 auto;
                min-width: 0;
            }
            .field-row .field-info small {
                color: var(--pf-global--Color--200);
            }
            .field-actions {
                display: flex;
                gap: var(--pf-global--spacer--xs);
            }
            .field-adders {
                display: flex;
                gap: var(--pf-global--spacer--sm);
                align-items: center;
                margin-top: var(--pf-global--spacer--md);
                flex-wrap: wrap;
            }
            .field-adders ak-search-select {
                flex-grow: 1;
            }
        `,
    ];

    _shouldRefresh = false;
    _timer = 0;

    connectedCallback(): void {
        super.connectedCallback();
        // Debounce preview refreshes to avoid spamming the API while editing.
        const minUpdateDelay = 1000;
        this._timer = setInterval(() => {
            if (this._shouldRefresh) {
                this.refreshPreview();
                this._shouldRefresh = false;
            }
        }, minUpdateDelay) as unknown as number;
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        clearInterval(this._timer);
    }

    public override reset(): void {
        super.reset();
        this.selectedFields = [];
        this.preview = null;
        this.previewError = null;
        this.previewResult = null;
    }

    protected override assignInstance(instance: PromptStage | null): void {
        super.assignInstance(instance);
        // Load the full prompt objects for display, preserving per-stage order.
        resolvePrompts(instance?.fields ?? []).then((prompts) => {
            this.selectedFields = prompts;
            this._shouldRefresh = true;
        });
    }

    public override toJSON(): PromptStage {
        // `fields` has no plain form control; inject the ordered UUIDs from our state.
        const data = super.toJSON();
        data.fields = this.selectedFields.map((prompt) => prompt.pk);
        return data;
    }

    // #region Field list mutation

    private onInnerRefresh = (event: Event): void => {
        // A nested ak-prompt-form (edit) was saved. Stop the event here so it doesn't bubble
        // out and refresh the stages table, then re-hydrate the edited fields for display.
        event.stopPropagation();
        resolvePrompts(this.selectedFields.map((prompt) => prompt.pk)).then((prompts) => {
            this.selectedFields = prompts;
            this._shouldRefresh = true;
        });
    };

    private onFieldCreated = (event: CustomEvent<Prompt>): void => {
        event.stopPropagation();
        this.addField(event.detail);
    };

    private reorderFields(keys: string[]): void {
        const byPk = new Map(this.selectedFields.map((prompt) => [prompt.pk, prompt]));
        this.selectedFields = keys
            .map((key) => byPk.get(key))
            .filter((prompt): prompt is Prompt => prompt !== undefined);
        this._shouldRefresh = true;
    }

    private addField(prompt: Prompt): void {
        if (this.selectedFields.some((field) => field.pk === prompt.pk)) {
            return;
        }
        this.selectedFields = [...this.selectedFields, prompt];
        this._shouldRefresh = true;
    }

    private removeField(pk: string): void {
        this.selectedFields = this.selectedFields.filter((field) => field.pk !== pk);
        this._shouldRefresh = true;
    }

    // #endregion

    // #region Preview

    async refreshPreview(): Promise<void> {
        return aki(StagesApi)
            .stagesPromptStagesPreviewCreate({
                promptStageRequest: {
                    name: this.instance?.name || "preview",
                    fields: this.selectedFields.map((prompt) => prompt.pk),
                },
            })
            .then((preview) => {
                this.preview = preview;
                this.previewError = null;
            })
            .catch(async (error: unknown) => {
                this.previewError = await parseAPIResponseError(error);
            });
    }

    renderPreview(): SlottedTemplateResult {
        return html`<h3 class="pf-c-title pf-m-lg">${msg("Preview")}</h3>
            <div class="pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-m-selectable pf-m-selected pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__body">
                        <ak-stage-prompt
                            .host=${new PreviewStageHost(this)}
                            .challenge=${this.preview}
                        ></ak-stage-prompt>
                    </div>
                </div>
                ${this.previewError
                    ? html`<div class="pf-c-card pf-l-grid__item pf-m-12-col">
                          <div class="pf-c-card__body">${msg("Preview errors")}</div>
                          <div class="pf-c-card__body">
                              ${AKFormErrors({ errors: [this.previewError] })}
                          </div>
                      </div>`
                    : nothing}
                ${this.previewResult
                    ? html`<div class="pf-c-card pf-l-grid__item pf-m-12-col">
                          <div class="pf-c-card__body">${msg("Data preview")}</div>
                          <div class="pf-c-card__body">
                              <pre>${JSON.stringify(this.previewResult, undefined, 4)}</pre>
                          </div>
                      </div>`
                    : nothing}
            </div>`;
    }

    // #endregion

    private renderFieldRow(prompt: Prompt): TemplateResult {
        return html`<div class="field-row" data-sortable-key=${prompt.pk}>
            <span class="handle" draggable="true" data-sortable-handle aria-hidden="true">
                <i class="fas fa-grip-vertical"></i>
            </span>
            <div class="field-info">
                <div>${prompt.name}</div>
                <small>${msg(str`"${prompt.fieldKey}", of type ${prompt.type}`)}</small>
            </div>
            <div class="field-actions">
                <ak-forms-modal size=${PFSize.XLarge}>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Prompt")}</span>
                    <ak-prompt-form slot="form" .instancePk=${prompt.pk}></ak-prompt-form>
                    <button type="button" slot="trigger" class="pf-c-button pf-m-secondary">
                        ${msg("Edit")}
                    </button>
                </ak-forms-modal>
                <button
                    type="button"
                    class="pf-c-button pf-m-danger pf-m-plain"
                    aria-label=${msg("Remove")}
                    @click=${() => this.removeField(prompt.pk)}
                >
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>`;
    }

    private renderFieldsEditor(): TemplateResult {
        // These listeners live on a container inside the shadow tree (not the host) so they
        // only see refresh/created events from the nested prompt forms below — never this
        // stage form's own success refresh, which is dispatched on the host above.
        return html`<div
            @ak-refresh=${this.onInnerRefresh}
            @ak-prompt-created=${this.onFieldCreated}
        >
            <ak-sortable-list
                @reorder=${(event: CustomEvent<{ keys: string[] }>) =>
                    this.reorderFields(event.detail.keys)}
            >
                ${this.selectedFields.length
                    ? repeat(
                          this.selectedFields,
                          (prompt) => prompt.pk,
                          (prompt) => this.renderFieldRow(prompt),
                      )
                    : html`<p class="pf-c-form__helper-text">
                          ${msg(
                              "No fields selected yet. Add an existing field or create a new one.",
                          )}
                      </p>`}
            </ak-sortable-list>
            <div class="field-adders">
                <ak-search-select
                    blankable
                    placeholder=${msg("Add an existing field...")}
                    .fetchObjects=${async (query?: string): Promise<Prompt[]> => {
                        const prompts = await aki(StagesApi).stagesPromptPromptsList({
                            ordering: "field_name,order",
                            pageSize: 20,
                            search: query ?? "",
                        });
                        return prompts.results;
                    }}
                    .renderElement=${(prompt: Prompt): string =>
                        `${prompt.name} ("${prompt.fieldKey}", of type ${prompt.type})`}
                    .value=${(prompt: Prompt | undefined): string | undefined => prompt?.pk}
                    @ak-change=${(event: CustomEvent<{ value: Prompt | undefined }>) => {
                        if (event.detail.value) {
                            this.addField(event.detail.value);
                        }
                    }}
                ></ak-search-select>
                <ak-forms-modal size=${PFSize.XLarge}>
                    <span slot="submit">${msg("Create")}</span>
                    <span slot="header">${msg("Create Prompt")}</span>
                    <ak-prompt-form slot="form"></ak-prompt-form>
                    <button type="button" slot="trigger" class="pf-c-button pf-m-primary">
                        ${msg("Create new field")}
                    </button>
                </ak-forms-modal>
            </div>
        </div>`;
    }

    protected override renderForm(): TemplateResult {
        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-l-grid__item pf-m-6-col pf-c-form pf-m-horizontal">
                ${this.renderEditForm()}
            </div>
            <div class="pf-l-grid__item pf-m-6-col">${this.renderPreview()}</div>
        </div> `;
    }

    protected renderEditForm(): TemplateResult {
        return html`<span>
                ${msg(
                    "Show arbitrary input fields to the user, for example during enrollment. Data is saved in the flow context under the 'prompt_data' variable.",
                )}
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
                    <ak-form-element-horizontal label=${msg("Fields")}>
                        ${this.renderFieldsEditor()}
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Fields are shown to the user in the order listed here. Drag to reorder.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Validation Policies")}
                        name="validationPolicies"
                    >
                        <ak-dual-select-dynamic-selected
                            .provider=${policiesProvider}
                            .selector=${policiesSelector(this.instance?.validationPolicies)}
                            available-label="${msg("Available Policies")}"
                            selected-label="${msg("Selected Policies")}"
                        ></ak-dual-select-dynamic-selected>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Selected policies are executed when the stage is submitted to validate the data.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-prompt-form": PromptStageForm;
    }
}
