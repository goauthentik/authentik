import "#admin/policies/BoundPoliciesList";
import "#admin/providers/rac/EndpointForm";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButton, ModalInvokerButton } from "#elements/dialogs";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { EndpointForm } from "#admin/providers/rac/EndpointForm";

import { Endpoint, ModelEnum, RacApi, RACProvider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-rac-endpoint-list")
export class EndpointListPage extends Table<Endpoint> {
    public static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    protected override searchEnabled = true;
    protected override emptyStateMessage = msg("Create an endpoint to get started.");

    public override expandable = true;
    public override checkbox = true;
    public override clearOnRefresh = true;

    public override searchPlaceholder = msg("Search for an endpoint by name or host...");
    public override order = "name";

    @property({ attribute: false })
    public provider: RACProvider | null = null;

    protected override async apiEndpoint(): Promise<PaginatedResponse<Endpoint>> {
        return new RacApi(DEFAULT_CONFIG).racEndpointsList({
            ...(await this.defaultEndpointConfig()),
            provider: this.provider?.pk,
            superuserFullList: true,
        });
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Host"), "host"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Endpoint(s)")}
            .objects=${this.selectedElements}
            .metadata=${(item: Endpoint) => {
                return [
                    { key: msg("Name"), value: item.name },
                    { key: msg("Host"), value: item.host },
                ];
            }}
            .usedBy=${(item: Endpoint) => {
                return new RacApi(DEFAULT_CONFIG).racEndpointsUsedByList({
                    pbmUuid: item.pk,
                });
            }}
            .delete=${(item: Endpoint) => {
                return new RacApi(DEFAULT_CONFIG).racEndpointsDestroy({
                    pbmUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: Endpoint): SlottedTemplateResult[] {
        return [
            item.name,
            item.host,
            html`<div class="ak-c-table__actions">
                ${IconEditButton(EndpointForm, item.pk)}

                <ak-rbac-object-permission-modal
                    model=${ModelEnum.AuthentikProvidersRacEndpoint}
                    objectPk=${item.pk}
                >
                </ak-rbac-object-permission-modal>
            </div>`,
        ];
    }

    protected override renderExpanded(item: Endpoint): SlottedTemplateResult {
        return html`<div class="pf-c-content">
            <p>
                ${msg(
                    "These bindings control which users will have access to this endpoint. Users must also have access to the application.",
                )}
            </p>
            <ak-bound-policies-list .target=${item.pk}></ak-bound-policies-list>
        </div>`;
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return ModalInvokerButton(EndpointForm, {
            providerID: this.provider?.pk,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rac-endpoint-list": EndpointListPage;
    }
}
