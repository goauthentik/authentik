import "#admin/outposts/ServiceConnectionDockerForm";
import "#admin/outposts/ServiceConnectionKubernetesForm";
import "#admin/outposts/ak-service-connection-wizard";
import "#admin/rbac/ObjectPermissionModal";
import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "#elements/tasks/ScheduleList";
import "#elements/tasks/TaskList";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButtonByTagName } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { PFColor } from "#elements/Label";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AKServiceConnectionWizard } from "#admin/outposts/ak-service-connection-wizard";

import {
    ModelEnum,
    OutpostsApi,
    ServiceConnection,
    ServiceConnectionState,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-outpost-service-connection-list")
export class OutpostServiceConnectionListPage extends TablePage<ServiceConnection> {
    public pageTitle = msg("Outpost integrations");
    public pageDescription = msg(
        "Outpost integrations define how authentik connects to external platforms to manage and deploy Outposts.",
    );

    public pageIcon = "pf-icon pf-icon-integration";
    protected override searchEnabled = true;

    public override checkbox = true;
    public override expandable = true;
    public override clearOnRefresh = true;
    public override searchPlaceholder = msg(
        "Search for an outpost integration by name, type or assigned integration...",
    );

    async apiEndpoint(): Promise<PaginatedResponse<ServiceConnection>> {
        const connections = await new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsAllList(
            await this.defaultEndpointConfig(),
        );
        await Promise.all(
            connections.results.map((connection) => {
                return new OutpostsApi(DEFAULT_CONFIG)
                    .outpostsServiceConnectionsAllStateRetrieve({
                        uuid: connection.pk,
                    })
                    .then((state) => {
                        this.state[connection.pk] = state;
                    });
            }),
        );
        return connections;
    }

    @state()
    state: { [key: string]: ServiceConnectionState } = {};

    protected columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type")],
        [msg("Local"), "local"],
        [msg("State")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    @property()
    order = "name";

    row(item: ServiceConnection): SlottedTemplateResult[] {
        const itemState = this.state[item.pk];
        return [
            item.name,
            item.verboseName,
            html`<ak-status-label type="info" ?good=${item.local}></ak-status-label>`,
            html`${itemState?.healthy
                ? html`<ak-label color=${PFColor.Green}>${ifDefined(itemState.version)}</ak-label>`
                : html`<ak-label color=${PFColor.Red}>${msg("Unhealthy")}</ak-label>`}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButtonByTagName(item.component, item.pk, item.verboseName)}
                ${IconPermissionButton(item.name, {
                    model: item.metaModelName as ModelEnum,
                    objectPk: item.pk,
                })}
            </div>`,
        ];
    }

    renderExpanded(item: ServiceConnection): TemplateResult {
        const [appLabel, modelName] = item.metaModelName.split(".");
        return html`<dl class="pf-c-description-list pf-m-horizontal">
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${msg("Schedules")}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            <ak-schedule-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${item.pk}"
                            ></ak-schedule-list>
                        </div>
                    </dd>
                </div>
            </dl>
            <dl class="pf-c-description-list pf-m-horizontal">
                <div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${msg("Tasks")}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">
                            <ak-task-list
                                .relObjAppLabel=${appLabel}
                                .relObjModel=${modelName}
                                .relObjId="${item.pk}"
                            ></ak-task-list>
                        </div>
                    </dd>
                </div>
            </dl>`;
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Outpost integration(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: ServiceConnection) => {
                return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsAllUsedByList({
                    uuid: item.pk,
                });
            }}
            .delete=${(item: ServiceConnection) => {
                return new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsAllDestroy({
                    uuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return html`<button
            class="pf-c-button pf-m-primary"
            type="button"
            aria-description="${msg("Open the wizard to create a new service connection.")}"
            ${AKServiceConnectionWizard.asModalInvoker()}
        >
            ${msg("New Outpost Integration")}
        </button>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-outpost-service-connection-list": OutpostServiceConnectionListPage;
    }
}
