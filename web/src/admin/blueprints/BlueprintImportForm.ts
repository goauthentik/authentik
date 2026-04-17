import "#components/ak-status-label";
import "#elements/events/LogViewer";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-toggle-group";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { Form } from "#elements/forms/Form";
import { PreventFormSubmit } from "#elements/forms/helpers";

import { AKLabel } from "#components/ak-label";

import { BlueprintSource } from "#admin/blueprints/BlueprintForm";

import {
    BlueprintFile,
    BlueprintImportResult,
    ManagedApi,
    ManagedBlueprintsImportCreateRequest,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

/**
 * @slot read-more-link - Link for the read more text
 * @slot banner-warning - Warning text below file upload
 */
@customElement("ak-blueprint-import-form")
export class BlueprintImportForm extends Form<ManagedBlueprintsImportCreateRequest> {
    static styles: CSSResult[] = [...super.styles, PFDescriptionList, PFBanner];

    public static override verboseName = msg("Flow Blueprint");
    public static override verboseNamePlural = msg("Flow Blueprints");
    public static override createLabel = msg("Import");
    public static override submitVerb = msg("Import");
    public static override submittingVerb = msg("Importing");

    public override size = PFSize.Medium;

    @state()
    protected result: BlueprintImportResult | null = null;

    @state()
    protected source: BlueprintSource = BlueprintSource.Upload;

    public override reset(): void {
        super.reset();

        this.source = BlueprintSource.Upload;
        this.result = null;
        this.nonFieldErrors = null;
    }

    getSuccessMessage(): string {
        return msg("Successfully imported blueprint.");
    }

    async send(data: ManagedBlueprintsImportCreateRequest): Promise<BlueprintImportResult> {
        if (this.source === BlueprintSource.Upload) {
            const file = this.files().get("blueprint");
            if (!file) {
                throw new PreventFormSubmit("No form data");
            }
            data.file = file;
        }
        const result = await new ManagedApi(DEFAULT_CONFIG).managedBlueprintsImportCreate(data);
        if (!result.success) {
            this.result = result;
            throw new PreventFormSubmit("Failed to import blueprint");
        }
        return result;
    }

    renderResult(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Successful")}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text">
                            <ak-status-label ?good=${this.result?.success}></ak-status-label>
                        </span>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Log messages")}>
                <ak-log-viewer .items=${this.result?.logs}></ak-log-viewer>
            </ak-form-element-horizontal>
        `;
    }

    protected override renderForm(): TemplateResult {
        return html` <ak-toggle-group
                value=${this.source}
                @ak-toggle=${(ev: CustomEvent<{ value: BlueprintSource }>) => {
                    this.reset();
                    this.source = ev.detail.value;
                }}
            >
                <option value=${BlueprintSource.Upload}>${msg("File upload")}</option>
                <option value=${BlueprintSource.File}>${msg("Local path")}</option>
            </ak-toggle-group>
            ${this.source === BlueprintSource.Upload
                ? html`
                      ${this.findSlotted("banner-warning")
                          ? html`<div class="pf-c-banner pf-m-warning" slot="above-form">
                                <slot name="banner-warning"></slot>
                            </div>`
                          : null}
                      <ak-form-element-horizontal name="blueprint">
                          ${AKLabel(
                              {
                                  slot: "label",
                                  className: "pf-c-form__group-label",
                                  htmlFor: "blueprint",
                              },
                              msg("Blueprint"),
                          )}

                          <input
                              type="file"
                              value=""
                              class="pf-c-form-control"
                              id="blueprint"
                              name="blueprint"
                              aria-describedby="blueprint-help"
                          />

                          <div id="blueprint-help">
                              <p class="pf-c-form__helper-text">
                                  ${msg(
                                      ".yaml files, which can be found in the Example Flows documentation",
                                  )}
                              </p>
                              ${this.findSlotted("read-more-link")
                                  ? html`<p class="pf-c-form__helper-text">
                                        ${msg("Read more about")}&nbsp;
                                        <slot name="read-more-link"></slot>
                                    </p>`
                                  : null}
                          </div>
                      </ak-form-element-horizontal>
                  `
                : null}
            ${this.source === BlueprintSource.File
                ? html`<ak-form-element-horizontal label=${msg("Path")} name="path">
                      <ak-search-select
                          placeholder=${msg("Select a blueprint...")}
                          .fetchObjects=${async (query?: string): Promise<BlueprintFile[]> => {
                              const items = await new ManagedApi(
                                  DEFAULT_CONFIG,
                              ).managedBlueprintsAvailableList();
                              return items.filter((item) =>
                                  query ? item.path.includes(query) : true,
                              );
                          }}
                          .renderElement=${(item: BlueprintFile): string => {
                              const name = item.path;
                              if (item.meta && item.meta.name) {
                                  return `${name} (${item.meta.name})`;
                              }
                              return name;
                          }}
                          .value=${(item: BlueprintFile | null) => {
                              return item?.path;
                          }}
                          blankable
                      >
                      </ak-search-select>
                  </ak-form-element-horizontal>`
                : nothing}
            ${this.result ? this.renderResult() : nothing}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-blueprint-import-form": BlueprintImportForm;
    }
}
