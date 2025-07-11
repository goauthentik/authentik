import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { parseAPIResponseError, pluckErrorDetail } from "@goauthentik/common/errors/network";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import { StageHost } from "@goauthentik/flow/stages/base";
import "@goauthentik/flow/stages/prompt/PromptStage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { map } from "lit/directives/map.js";

import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import {
    Prompt,
    PromptChallenge,
    PromptTypeEnum,
    StagesApi,
    instanceOfValidationError,
} from "@goauthentik/api";

class PreviewStageHost implements StageHost {
    challenge = undefined;
    flowSlug = undefined;
    loading = false;
    brand = undefined;
    async submit(payload: unknown): Promise<boolean> {
        this.promptForm.previewResult = payload;
        return false;
    }

    constructor(private promptForm: PromptForm) {}
}

@customElement("ak-prompt-form")
export class PromptForm extends ModelForm<Prompt, string> {
    @state()
    preview?: PromptChallenge;

    @state()
    previewError?: string[];

    @state()
    previewResult: unknown;

    send(data: Prompt): Promise<unknown> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsUpdate({
                promptUuid: this.instance.pk || "",
                promptRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsCreate({
                promptRequest: data,
            });
        }
    }

    async loadInstance(pk: string): Promise<Prompt> {
        const prompt = await new StagesApi(DEFAULT_CONFIG).stagesPromptPromptsRetrieve({
            promptUuid: pk,
        });
        await this.refreshPreview(prompt);
        return prompt;
    }

    async refreshPreview(prompt?: Prompt): Promise<void> {
        if (!prompt) {
            prompt = this.serializeForm();
            if (!prompt) {
                return;
            }
        }

        return new StagesApi(DEFAULT_CONFIG)
            .stagesPromptPromptsPreviewCreate({
                promptRequest: prompt,
            })
            .then((nextPreview) => {
                this.preview = nextPreview;
                this.previewError = undefined;
            })
            .catch(async (error: unknown) => {
                const parsedError = await parseAPIResponseError(error);

                this.previewError = instanceOfValidationError(parsedError)
                    ? parsedError.nonFieldErrors
                    : [pluckErrorDetail(parsedError, msg("Failed to preview prompt"))];
            });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated prompt.")
            : msg("Successfully created prompt.");
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(PFGrid, PFTitle);
    }

    _shouldRefresh = false;
    _timer = 0;

    connectedCallback(): void {
        super.connectedCallback();
        // Only check if we should update once a second, to prevent spamming API requests
        // when many fields are edited
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
        clearTimeout(this._timer);
    }

    renderTypes(): TemplateResult {
        // prettier-ignore
        const promptTypesWithLabels = [
            [PromptTypeEnum.Text, msg("Text: Simple Text input")],
            [PromptTypeEnum.TextArea, msg("Text Area: Multiline text input")],
            [PromptTypeEnum.TextReadOnly, msg("Text (read-only): Simple Text input, but cannot be edited.")],
            [PromptTypeEnum.TextAreaReadOnly, msg("Text Area (read-only): Multiline text input, but cannot be edited.")],
            [PromptTypeEnum.Username, msg("Username: Same as Text input, but checks for and prevents duplicate usernames.")],
            [PromptTypeEnum.Email, msg("Email: Text field with Email type.")],
            [PromptTypeEnum.Password, msg("Password: Masked input, multiple inputs of this type on the same prompt need to be identical.")],
            [PromptTypeEnum.Number, msg("Number")],
            [PromptTypeEnum.Checkbox, msg("Checkbox")],
            [PromptTypeEnum.RadioButtonGroup, msg("Radio Button Group (fixed choice)")],
            [PromptTypeEnum.Dropdown, msg("Dropdown (fixed choice)")],
            [PromptTypeEnum.Date, msg("Date")],
            [PromptTypeEnum.DateTime, msg("Date Time")],
            [PromptTypeEnum.File, msg("File")],
            [PromptTypeEnum.Separator, msg("Separator: Static Separator Line")],
            [PromptTypeEnum.Hidden, msg("Hidden: Hidden field, can be used to insert data into form.")],
            [PromptTypeEnum.Static, msg("Static: Static value, displayed as-is.")],
            [PromptTypeEnum.AkLocale, msg("authentik: Locale: Displays a list of locales authentik supports.")],
        ];
        const currentType = this.instance?.type;
        return html` ${map(
            promptTypesWithLabels,
            ([promptType, label]) =>
                html`<option value=${promptType} ?selected=${promptType === currentType}>
                    ${label}
                </option>`,
        )}`;
    }

    renderForm(): TemplateResult {
        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-l-grid__item pf-m-6-col pf-c-form pf-m-horizontal">
                ${this.renderEditForm()}
            </div>
            <div class="pf-l-grid__item pf-m-6-col">${this.renderPreview()}</div>
        </div> `;
    }

    renderPreview(): TemplateResult {
        return html`
            <h3 class="pf-c-title pf-m-lg">${msg("Preview")}</h3>
            <div class="pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-m-selectable pf-m-selected pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__body">
                        <ak-stage-prompt
                            .host=${new PreviewStageHost(this)}
                            .challenge=${this.preview}
                        >
                        </ak-stage-prompt>
                    </div>
                </div>
                ${this.previewError
                    ? html`
                          <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                              <div class="pf-c-card__body">${msg("Preview errors")}</div>
                              <div class="pf-c-card__body">
                                  ${this.previewError.map((err) => html`<pre>${err}</pre>`)}
                              </div>
                          </div>
                      `
                    : html``}
                ${this.previewResult
                    ? html`
                          <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                              <div class="pf-c-card__body">${msg("Data preview")}</div>
                              <div class="pf-c-card__body">
                                  <pre>${JSON.stringify(this.previewResult, undefined, 4)}</pre>
                              </div>
                          </div>
                      `
                    : html``}
            </div>
        `;
    }

    renderEditForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                    @input=${() => {
                        this._shouldRefresh = true;
                    }}
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Unique name of this field, used for selecting fields in prompt stages.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Field Key")} ?required=${true} name="fieldKey">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.fieldKey)}"
                    class="pf-c-form-control pf-m-monospace"
                    autocomplete="off"
                    spellcheck="false"
                    required
                    @input=${() => {
                        this._shouldRefresh = true;
                    }}
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Name of the form field, also used to store the value.")}
                </p>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When used in conjunction with a User Write stage, use attributes.foo to write attributes.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Label")} ?required=${true} name="label">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.label)}"
                    class="pf-c-form-control"
                    required
                    @input=${() => {
                        this._shouldRefresh = true;
                    }}
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Label shown next to/above the prompt.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Type")} ?required=${true} name="type">
                <select
                    class="pf-c-form-control"
                    @change=${() => {
                        this._shouldRefresh = true;
                    }}
                >
                    ${this.renderTypes()}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="required">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.required, false)}
                        @change=${() => {
                            this._shouldRefresh = true;
                        }}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Required")}</span>
                </label>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="placeholderExpression">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.placeholderExpression, false)}
                        @change=${() => {
                            this._shouldRefresh = true;
                        }}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label"
                        >${msg("Interpret placeholder as expression")}</span
                    >
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        `When checked, the placeholder will be evaluated in the same way a property mapping is.
            If the evaluation fails, the placeholder itself is returned.`,
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Placeholder")} name="placeholder">
                <ak-codemirror
                    mode=${CodeMirrorMode.Python}
                    value="${ifDefined(this.instance?.placeholder)}"
                    @change=${() => {
                        this._shouldRefresh = true;
                    }}
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        `Optionally provide a short hint that describes the expected input value.
            When creating a fixed choice field, enable interpreting as expression and return a
        list to return multiple choices.`,
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="initialValueExpression">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.initialValueExpression, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label"
                        >${msg("Interpret initial value as expression")}</span
                    >
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        `When checked, the initial value will be evaluated in the same way a property mapping is.
            If the evaluation fails, the initial value itself is returned.`,
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Initial value")} name="initialValue">
                <ak-codemirror
                    mode=${CodeMirrorMode.Python}
                    value="${ifDefined(this.instance?.initialValue)}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        `Optionally pre-fill the input with an initial value.
            When creating a fixed choice field, enable interpreting as expression and
        return a list to return multiple default choices.`,
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Help text")} name="subText">
                <ak-codemirror
                    mode=${CodeMirrorMode.HTML}
                    value="${ifDefined(this.instance?.subText)}"
                    @change=${() => {
                        this._shouldRefresh = true;
                    }}
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">${msg("Any HTML can be used.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Order")} ?required=${true} name="order">
                <input
                    type="number"
                    value="${first(this.instance?.order, 0)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-prompt-form": PromptForm;
    }
}
