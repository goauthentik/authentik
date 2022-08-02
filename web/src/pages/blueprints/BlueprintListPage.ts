import { AKResponse } from "@goauthentik/web/api/Client";
import { DEFAULT_CONFIG } from "@goauthentik/web/api/Config";
import { uiConfig } from "@goauthentik/web/common/config";
import { PFColor } from "@goauthentik/web/elements/Label";
import "@goauthentik/web/elements/buttons/SpinnerButton";
import "@goauthentik/web/elements/forms/DeleteBulkForm";
import "@goauthentik/web/elements/forms/ModalForm";
import { TableColumn } from "@goauthentik/web/elements/table/Table";
import { TablePage } from "@goauthentik/web/elements/table/TablePage";
import "@goauthentik/web/pages/blueprints/BlueprintForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { BlueprintInstance, ManagedApi } from "@goauthentik/api";

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

    async apiEndpoint(page: number): Promise<AKResponse<BlueprintInstance>> {
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
        const delta = Date.now() - item.lastApplied.getTime();
        const ago = Math.round(delta / 1000 / 3600);
        const applyDelta = t`${ago} hours ago`;
        return [
            html`${item.name}`,
            html`${item.status}`,
            html`${applyDelta}`,
            html`<ak-label color=${item.enabled ? PFColor.Green : PFColor.Red}>
                ${item.enabled ? t`Yes` : t`No`}
            </ak-label>`,
            html`<ak-forms-modal>
                <span slot="submit"> ${t`Update`} </span>
                <span slot="header"> ${t`Update Blueprint`} </span>
                <ak-blueprint-form slot="form" .instancePk=${item.pk}> </ak-blueprint-form>
                <button slot="trigger" class="pf-c-button pf-m-plain">
                    <i class="fas fa-edit"></i>
                </button>
            </ak-forms-modal>`,
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
