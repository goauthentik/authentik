import "@goauthentik/admin/property-mappings/PropertyMappingLDAPForm";
import "@goauthentik/admin/property-mappings/PropertyMappingNotification";
import "@goauthentik/admin/property-mappings/PropertyMappingSAMLForm";
import "@goauthentik/admin/property-mappings/PropertyMappingSCIMForm";
import "@goauthentik/admin/property-mappings/PropertyMappingScopeForm";
import "@goauthentik/admin/property-mappings/PropertyMappingTestForm";
import "@goauthentik/admin/property-mappings/PropertyMappingWizard";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/forms/DeleteBulkForm";
import "@goauthentik/elements/forms/ModalForm";
import "@goauthentik/elements/forms/ProxyForm";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { t } from "@lingui/macro";

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
        return t`Property Mappings`;
    }
    pageDescription(): string {
        return t`Control how authentik exposes and interprets information.`;
    }
    pageIcon(): string {
        return "pf-icon pf-icon-blueprint";
    }

    checkbox = true;

    @property()
    order = "name";

    @state()
    hideManaged = getURLParam<boolean>("hideManaged", true);

    async apiEndpoint(page: number): Promise<PaginatedResponse<PropertyMapping>> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            managedIsnull: this.hideManaged ? true : undefined,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(t`Name`, "name"),
            new TableColumn(t`Type`, "type"),
            new TableColumn(t`Actions`),
        ];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`Property Mapping(s)`}
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
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: PropertyMapping): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.verboseName}`,
            html` <ak-forms-modal>
                    <span slot="submit"> ${t`Update`} </span>
                    <span slot="header"> ${t`Update ${item.verboseName}`} </span>
                    <ak-proxy-form
                        slot="form"
                        .args=${{
                            instancePk: item.pk,
                        }}
                        type=${ifDefined(item.component)}
                    >
                    </ak-proxy-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-edit"></i>
                    </button>
                </ak-forms-modal>
                <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                    <span slot="submit"> ${t`Test`} </span>
                    <span slot="header"> ${t`Test Property Mapping`} </span>
                    <ak-property-mapping-test-form slot="form" .mapping=${item}>
                    </ak-property-mapping-test-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <i class="fas fa-vial" aria-hidden="true"></i>
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
                            <span class="pf-c-switch__label">${t`Hide managed mappings`}</span>
                        </label>
                    </div>
                </div>
            </div>`;
    }
}
