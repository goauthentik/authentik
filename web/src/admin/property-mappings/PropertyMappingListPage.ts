import "#admin/property-mappings/PropertyMappingNotification";
import "#admin/property-mappings/PropertyMappingProviderGoogleWorkspaceForm";
import "#admin/property-mappings/PropertyMappingProviderMicrosoftEntraForm";
import "#admin/property-mappings/PropertyMappingProviderRACForm";
import "#admin/property-mappings/PropertyMappingProviderRadiusForm";
import "#admin/property-mappings/PropertyMappingProviderSAMLForm";
import "#admin/property-mappings/PropertyMappingProviderSCIMForm";
import "#admin/property-mappings/PropertyMappingProviderScopeForm";
import "#admin/property-mappings/PropertyMappingSourceKerberosForm";
import "#admin/property-mappings/PropertyMappingSourceLDAPForm";
import "#admin/property-mappings/PropertyMappingSourceOAuthForm";
import "#admin/property-mappings/PropertyMappingSourcePlexForm";
import "#admin/property-mappings/PropertyMappingSourceSAMLForm";
import "#admin/property-mappings/PropertyMappingSourceSCIMForm";
import "#admin/property-mappings/PropertyMappingSourceTelegramForm";
import "#admin/property-mappings/PropertyMappingTestForm";
import "#admin/property-mappings/ak-property-mapping-wizard";
import "#admin/rbac/ObjectPermissionModal";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { IconEditButtonByTagName, modalInvoker } from "#elements/dialogs";
import { IconPermissionButton } from "#elements/dialogs/components/IconPermissionButton";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import { AKPropertyMappingWizard } from "#admin/property-mappings/ak-property-mapping-wizard";
import { PropertyMappingTestForm } from "#admin/property-mappings/PropertyMappingTestForm";

import { ModelEnum, PropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-property-mapping-list")
export class PropertyMappingListPage extends TablePage<PropertyMapping> {
    protected override searchEnabled = true;
    public override pageTitle = msg("Property Mappings");
    public override pageDescription = msg(
        "Control how authentik exposes and interprets information.",
    );
    public override pageIcon = "pf-icon pf-icon-blueprint";
    public override searchPlaceholder = msg("Search for a property mapping by name or type...");

    public override checkbox = true;
    public override clearOnRefresh = true;

    public override order = "name";

    @state()
    protected hideManaged = getURLParam<boolean>("hideManaged", true);

    protected override async apiEndpoint(): Promise<PaginatedResponse<PropertyMapping>> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllList({
            ...(await this.defaultEndpointConfig()),
            managedIsnull: this.hideManaged ? true : undefined,
        });
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "name"],
        [msg("Type"), "type"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    protected override renderToolbarSelected(): SlottedTemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            object-label=${msg("Property Mapping(s)")}
            .objects=${this.selectedElements}
            .usedBy=${(item: PropertyMapping) => {
                return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllUsedByList({
                    pmUuid: item.pk,
                });
            }}
            .delete=${(item: PropertyMapping) => {
                return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllDestroy({
                    pmUuid: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected override row(item: PropertyMapping): SlottedTemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.verboseName}`,
            html`<div class="ak-c-table__actions">
                ${IconEditButtonByTagName(item.component, item.pk)}
                ${IconPermissionButton(item.name, {
                    model: item.metaModelName as ModelEnum,
                    objectPk: item.pk,
                })}

                <button
                    class="pf-c-button pf-m-plain"
                    ${modalInvoker(
                        PropertyMappingTestForm,
                        { mapping: item },
                        {
                            closedBy: "closerequest",
                        },
                    )}
                >
                    <pf-tooltip position="top" content=${msg("Test")}>
                        <i class="fas fa-vial" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </div>`,
        ];
    }

    protected override renderObjectCreate(): SlottedTemplateResult {
        return html`<button
            class="pf-c-button pf-m-primary"
            ${modalInvoker(AKPropertyMappingWizard)}
        >
            ${msg("New Property Mapping")}
        </button>`;
    }

    protected override renderToolbarAfter(): SlottedTemplateResult {
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <div class="pf-c-input-group">
                    <label class="pf-c-switch">
                        <input
                            class="pf-c-switch__input"
                            type="checkbox"
                            ?checked=${this.hideManaged}
                            @change=${() => {
                                this.hideManaged = !this.hideManaged;
                                this.page = 1;
                                this.fetch();
                                updateURLParams({
                                    hideManaged: this.hideManaged,
                                });
                            }}
                        />
                        <span class="pf-c-switch__toggle">
                            <span class="pf-c-switch__toggle-icon">
                                <i class="fas fa-check" aria-hidden="true"></i>
                            </span>
                        </span>
                        <span class="pf-c-switch__label">${msg("Hide managed mappings")}</span>
                    </label>
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-list": PropertyMappingListPage;
    }
}
