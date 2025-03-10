import "@goauthentik/admin/property-mappings/PropertyMappingNotification";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderGoogleWorkspaceForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderMicrosoftEntraForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderRACForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderRadiusForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderSAMLForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderSCIMForm";
import "@goauthentik/admin/property-mappings/PropertyMappingProviderScopeForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceKerberosForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceLDAPForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceOAuthForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourcePlexForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceSAMLForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSourceSCIMForm";
import "@goauthentik/admin/property-mappings/PropertyMappingTestForm";
import "@goauthentik/admin/property-mappings/PropertyMappingWizard";
import "@goauthentik/admin/rbac/ObjectPermissionModal";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg, str } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { PropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-list")
export class PropertyMappingListPage extends TablePage<PropertyMapping> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return msg("Property Mappings");
    }
    pageDescription(): string {
        return msg("Control how authentik exposes and interprets information.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-blueprint";
    }

    checkbox = true;
    clearOnRefresh = true;

    @property()
    order = "name";

    @state()
    hideManaged = getURLParam<boolean>("hideManaged", true);

    async apiEndpoint(): Promise<PaginatedResponse<PropertyMapping>> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllList({
            ...(await this.defaultEndpointConfig()),
            managedIsnull: this.hideManaged ? true : undefined,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Type"), "type"),
            new TableColumn(msg("Actions")),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Property Mapping(s)")}
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

    row(item: PropertyMapping): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.verboseName}`,
            html` <ak-forms-modal>
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
                <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                    <span slot="submit"> ${msg("Test")} </span>
                    <span slot="header"> ${msg("Test Property Mapping")} </span>
                    <ak-property-mapping-test-form slot="form" .mapping=${item}>
                    </ak-property-mapping-test-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Test")}>
                            <i class="fas fa-vial" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>`,
        ];
    }

    renderObjectCreate(): TemplateResult {
        return html`<ak-property-mapping-wizard></ak-property-mapping-wizard> `;
    }

    renderToolbarAfter(): TemplateResult {
        return html`&nbsp;
            <div class="pf-c-toolbar__group pf-m-filter-group">
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
