import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { PropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { AKResponse } from "../../api/Client";
import { DEFAULT_CONFIG } from "../../api/Config";
import { uiConfig } from "../../common/config";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteBulkForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ProxyForm";
import { TableColumn } from "../../elements/table/Table";
import { TablePage } from "../../elements/table/TablePage";
import { groupBy } from "../../utils";
import "./PropertyMappingLDAPForm";
import "./PropertyMappingNotification";
import "./PropertyMappingSAMLForm";
import "./PropertyMappingScopeForm";
import "./PropertyMappingTestForm";

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

    @property({ type: Boolean })
    hideManaged = false;

    async apiEndpoint(page: number): Promise<AKResponse<PropertyMapping>> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
            managedIsnull: this.hideManaged ? true : undefined,
        });
    }

    groupBy(items: PropertyMapping[]): [string, PropertyMapping[]][] {
        return groupBy(items, (mapping) => mapping.verboseNamePlural);
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

    renderToolbar(): TemplateResult {
        return html` <ak-dropdown class="pf-c-dropdown">
                <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                    <span class="pf-c-dropdown__toggle-text">${t`Create`}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <ul class="pf-c-dropdown__menu" hidden>
                    ${until(
                        new PropertymappingsApi(DEFAULT_CONFIG)
                            .propertymappingsAllTypesList()
                            .then((types) => {
                                return types.map((type) => {
                                    return html`<li>
                                        <ak-forms-modal>
                                            <span slot="submit"> ${t`Create`} </span>
                                            <span slot="header"> ${t`Create ${type.name}`} </span>
                                            <ak-proxy-form slot="form" type=${type.component}>
                                            </ak-proxy-form>
                                            <button slot="trigger" class="pf-c-dropdown__menu-item">
                                                ${type.name}<br />
                                                <small>${type.description}</small>
                                            </button>
                                        </ak-forms-modal>
                                    </li>`;
                                });
                            }),
                        html`<ak-spinner></ak-spinner>`,
                    )}
                </ul>
            </ak-dropdown>
            ${super.renderToolbar()}`;
    }

    renderToolbarAfter(): TemplateResult {
        return html`&nbsp;
            <div class="pf-c-toolbar__group pf-m-filter-group">
                <div class="pf-c-toolbar__item pf-m-search-filter">
                    <div class="pf-c-input-group">
                        <div class="pf-c-check">
                            <input
                                class="pf-c-check__input"
                                type="checkbox"
                                id="hide-managed"
                                name="hide-managed"
                                ?checked=${this.hideManaged}
                                @change=${() => {
                                    this.hideManaged = !this.hideManaged;
                                    this.page = 1;
                                    this.fetch();
                                }}
                            />
                            <label class="pf-c-check__label" for="hide-managed"
                                >${t`Hide managed mappings`}</label
                            >
                        </div>
                    </div>
                </div>
            </div>`;
    }
}
