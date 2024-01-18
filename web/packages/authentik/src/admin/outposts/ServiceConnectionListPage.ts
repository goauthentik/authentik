import "@goauthentik/admin/outposts/OutpostHealth";
import "@goauthentik/admin/outposts/ServiceConnectionDockerForm";
import "@goauthentik/admin/outposts/ServiceConnectionKubernetesForm";
import "@goauthentik/admin/outposts/ServiceConnectionWizard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import { uiConfig } from "@goauthentik/common/ui/config.js";
import "@goauthentik/components/ak-status-label";
import { PFColor } from "@goauthentik/elements/Label.js";
import "@goauthentik/elements/buttons/SpinnerButton/ak-spinner-button.js";
import "@goauthentik/elements/forms/DeleteBulkForm.js";
import "@goauthentik/elements/forms/ModalForm.js";
import "@goauthentik/elements/forms/ProxyForm.js";
import "@goauthentik/elements/rbac/ObjectPermissionModal.js";
import { PaginatedResponse } from "@goauthentik/elements/table/Table.js";
import { TableColumn } from "@goauthentik/elements/table/Table.js";
import { TablePage } from "@goauthentik/elements/table/TablePage.js";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { OutpostsApi, ServiceConnection, ServiceConnectionState } from "@goauthentik/api";

@customElement("ak-outpost-service-connection-list")
export class OutpostServiceConnectionListPage extends TablePage<ServiceConnection> {
    pageTitle(): string {
        return "Outpost integrations";
    }
    pageDescription(): string | undefined {
        return "Outpost integrations define how authentik connects to external platforms to manage and deploy Outposts.";
    }
    pageIcon(): string {
        return "pf-icon pf-icon-integration";
    }
    searchEnabled(): boolean {
        return true;
    }

    checkbox = true;

    async apiEndpoint(page: number): Promise<PaginatedResponse<ServiceConnection>> {
        const connections = await new OutpostsApi(DEFAULT_CONFIG).outpostsServiceConnectionsAllList(
            {
                ordering: this.order,
                page: page,
                pageSize: (await uiConfig()).pagination.perPage,
                search: this.search || "",
            },
        );
        Promise.all(
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

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Type")),
            new TableColumn(msg("Local"), "local"),
            new TableColumn(msg("State")),
            new TableColumn(msg("Actions")),
        ];
    }

    @property()
    order = "name";

    row(item: ServiceConnection): TemplateResult[] {
        const itemState = this.state[item.pk];
        return [
            html`${item.name}`,
            html`${item.verboseName}`,
            html`<ak-status-label type="info" ?good=${item.local}></ak-status-label>`,
            html`${itemState?.healthy
                ? html`<ak-label color=${PFColor.Green}>${ifDefined(itemState.version)}</ak-label>`
                : html`<ak-label color=${PFColor.Red}>${msg("Unhealthy")}</ak-label>`}`,
            html`
                <ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg(str`Update ${item.verboseName}`)} </span>
                    <ak-proxy-form
                        slot="form"
                        .args=${{
                            instancePk: item.pk,
                        }}
                        type=${ifDefined(item.component)}
                    >
                    </ak-proxy-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                <ak-rbac-object-permission-modal model=${item.metaModelName} objectPk=${item.pk}>
                </ak-rbac-object-permission-modal>
            `,
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Outpost integration(s)")}
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

    renderObjectCreate(): TemplateResult {
        return html`<ak-service-connection-wizard></ak-service-connection-wizard> `;
    }
}
