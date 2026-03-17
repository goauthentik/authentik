import "#admin/stages/register";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { CustomFormElementTagName } from "#elements/forms/unsafe";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";
import { StrictUnsafe } from "#elements/utils/unsafe";

import { Stage, StagesApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-stage-list")
export class StageListPage extends TablePage<Stage> {
    public pageTitle = msg("Stages");
    public pageDescription = msg(
        "Stages are single steps of a Flow that a user is guided through. A stage can only be executed from within a flow.",
    );
    public pageIcon = "pf-icon pf-icon-plugged";
    protected override searchEnabled = true;

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    async apiEndpoint(): Promise<PaginatedResponse<Stage>> {
        return new StagesApi(DEFAULT_CONFIG).stagesAllList(await this.defaultEndpointConfig());
    }

    protected columns: TableColumn[] = [
        // ---
        [msg("Name"), "name"],
        [msg("Flows")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Stage(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Stage) => {
                return new StagesApi(DEFAULT_CONFIG).stagesAllUsedByList({
                    stageUuid: item.pk,
                });
            }}
            .delete=${(item: Stage) => {
                return new StagesApi(DEFAULT_CONFIG).stagesAllDestroy({
                    stageUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    renderStageActions(stage: Stage) {
        return stage.component === "ak-stage-authenticator-duo-form"
            ? html`<ak-forms-modal>
                  <span slot="submit">${msg("Import")}</span>
                  <span slot="header">${msg("Import Duo device")}</span>
                  <ak-stage-authenticator-duo-device-import-form
                      slot="form"
                      .instancePk=${stage.pk}
                  >
                  </ak-stage-authenticator-duo-device-import-form>
                  <button slot="trigger" class="pf-c-button pf-m-plain">
                      <pf-tooltip position="top" content=${msg("Import devices")}>
                          <i class="fas fa-file-import" aria-hidden="true"></i>
                      </pf-tooltip>
                  </button>
              </ak-forms-modal>`
            : nothing;
    }

    row(item: Stage): SlottedTemplateResult[] {
        return [
            html`<div>${item.name}</div>
                <small>${item.verboseName}</small>`,
            html`<ul class="pf-c-list">
                ${item.flowSet?.map((flow) => {
                    return html`<li>
                        <a href="#/flow/flows/${flow.slug}">
                            <code>${flow.slug}</code>
                        </a>
                    </li>`;
                })}
            </ul>`,
            html`<div>
                <ak-forms-modal>
                    ${StrictUnsafe<CustomFormElementTagName>(item.component, {
                        slot: "form",
                        instancePk: item.pk,
                        actionLabel: msg("Update"),
                        headline: msg(str`Update ${item.verboseName}`, {
                            id: "form.headline.update",
                        }),
                    })}
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal model=${item.metaModelName} objectPk=${item.pk}>
                </ak-rbac-object-permission-modal>
                ${this.renderStageActions(item)}
            </div>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-stage-wizard></ak-stage-wizard> `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-stage-list": StageListPage;
    }
}
