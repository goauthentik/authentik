import "@goauthentik/admin/blueprints/BlueprintForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PFColor } from "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { BlueprintInstance, BlueprintInstanceStatusEnum, ManagedApi } from "@goauthentik/api";

export function BlueprintStatus(blueprint?: BlueprintInstance): string {
    if (!blueprint) return "";
    switch (blueprint.status) {
        case BlueprintInstanceStatusEnum.Successful:
            return t`Successful`;
        case BlueprintInstanceStatusEnum.Orphaned:
            return t`Orphaned`;
        case BlueprintInstanceStatusEnum.Warning:
            return t`Warning`;
        case BlueprintInstanceStatusEnum.Error:
            return t`Error`;
    }
    return t`Unknown`;
}

@customElement("ak-blueprint-list")
export class BlueprintListPage extends TablePage<BlueprintInstance> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`Blueprints`;
    }
    pageDescription(): string {
        return t`Automate and template configuration within authentik.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-blueprint";
    }

    checkbox = true;

    @property()
    order = "name";

    async apiEndpoint(page: number): Promise<PaginatedResponse<BlueprintInstance>> {
        return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Status`, "status"),
            new TableColumn(t`Last applied`, "last_applied"),
            new TableColumn(t`Enabled`, "enabled"),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Blueprint(s)`}
            .objects=${this.selectedElements}
            .metadata=${(item: BlueprintInstance) => {
                return [{ key: t`Name`, value: item.name }];
            }}
            .usedBy=${(item: BlueprintInstance) => {
                return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsUsedByList({
                    instanceUuid: item.pk,
                });
            }}
            .delete=${(item: BlueprintInstance) => {
                return new ManagedApi(DEFAULT_CONFIG).managedBlueprintsDestroy({
                    instanceUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: BlueprintInstance): TemplateResult[] {
        let description = undefined;
        const descKey = "blueprints.goauthentik.io/description";
        if (Object.hasOwn(item.metadata.labels, descKey)) {
            description = item.metadata.labels[descKey];
        }
        return [
            html`<div>${item.name}</div>
                ${description ? html`<small>${description}</small>` : html``}`,
            html`${BlueprintStatus(item)}`,
            html`${item.lastApplied.toLocaleString()}`,
            html`<ak-label color=${item.enabled ? PFColor.Green : PFColor.Red}>
                ${item.enabled ? t`Yes` : t`No`}
            </ak-label>`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update Blueprint`} </span>
                    <ak-blueprint-form slot="form" .instancePk=${item.pk}> </ak-blueprint-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button> </ak-forms-modal
                ><ak-action-button
                    class="pf-m-plain"
                    .apiRequest=${() => {
                        return new ManagedApi(DEFAULT_CONFIG)
                            .managedBlueprintsApplyCreate({
                                instanceUuid: item.pk,
                            })
                            .then(() => {
                                this.dispatchEvent(
                                    new CustomEvent(EVENT_REFRESH, {
                                        bubbles: true,
                                        composed: true,
                                    }),
                                );
                            });
                    }}
                >
                    <i class="fas fa-play" aria-hidden="true"></i>
                </ak-action-button>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`
            <ak-forms-modal>
                <span slot="submit"> ${t`Create`} </span>
                <span slot="header"> ${t`Create Blueprint Instance`} </span>
                <ak-blueprint-form slot="form"> </ak-blueprint-form>
                <button slot="trigger" class="pf-c-button pf-m-primary">${t`Create`}</button>
            </ak-forms-modal>
        `;
    }
}
