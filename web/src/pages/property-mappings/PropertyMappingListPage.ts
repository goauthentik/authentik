import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import "../../elements/forms/DeleteForm";
import "../../elements/forms/ModalForm";
import "../../elements/forms/ProxyForm";
import "./PropertyMappingTestForm";
import "./PropertyMappingScopeForm";
import "./PropertyMappingLDAPForm";
import "./PropertyMappingSAMLForm";
import { TableColumn } from "../../elements/table/Table";
import { until } from "lit-html/directives/until";
import { PAGE_SIZE } from "../../constants";
import { PropertyMapping, PropertymappingsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ifDefined } from "lit-html/directives/if-defined";

@customElement("ak-property-mapping-list")
export class PropertyMappingListPage extends TablePage<PropertyMapping> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return gettext("Property Mappings");
    }
    pageDescription(): string {
        return gettext("Control how authentik exposes and interprets information.");
    }
    pageIcon(): string {
        return "pf-icon pf-icon-blueprint";
    }

    @property()
    order = "name";

    @property({type: Boolean})
    hideManaged = false;

    apiEndpoint(page: number): Promise<AKResponse<PropertyMapping>> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
            managedIsnull: this.hideManaged ? "true" : undefined,
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Name", "name"),
            new TableColumn("Type", "type"),
            new TableColumn(""),
        ];
    }

    row(item: PropertyMapping): TemplateResult[] {
        return [
            html`${item.name}`,
            html`${item.verboseName}`,
            html`
            <ak-forms-modal>
                <span slot="submit">
                    ${gettext("Update")}
                </span>
                <span slot="header">
                    ${gettext(`Update ${item.verboseName}`)}
                </span>
                <ak-proxy-form
                    slot="form"
                    .args=${{
                        "mappingUUID": item.pk
                    }}
                    type=${ifDefined(item.component)}>
                </ak-proxy-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Edit")}
                </button>
            </ak-forms-modal>
            <ak-forms-modal .closeAfterSuccessfulSubmit=${false}>
                <span slot="submit">
                    ${gettext("Test")}
                </span>
                <span slot="header">
                    ${gettext("Test Property Mapping")}
                </span>
                <ak-property-mapping-test-form slot="form" .mapping=${item}>
                </ak-property-mapping-test-form>
                <button slot="trigger" class="pf-c-button pf-m-secondary">
                    ${gettext("Test")}
                </button>
            </ak-forms-modal>
            <ak-forms-delete
                .obj=${item}
                objectLabel=${gettext("Property Mapping")}
                .delete=${() => {
                    return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllDelete({
                        pmUuid: item.pk || ""
                    });
                }}>
                <button slot="trigger" class="pf-c-button pf-m-danger">
                    ${gettext("Delete")}
                </button>
            </ak-forms-delete>`,
        ];
    }

    renderToolbar(): TemplateResult {
        return html`
        <ak-dropdown class="pf-c-dropdown">
            <button class="pf-m-primary pf-c-dropdown__toggle" type="button">
                <span class="pf-c-dropdown__toggle-text">${gettext("Create")}</span>
                <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
            </button>
            <ul class="pf-c-dropdown__menu" hidden>
                ${until(new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsAllTypes().then((types) => {
                    return types.map((type) => {
                        return html`<li>
                            <ak-forms-modal>
                                <span slot="submit">
                                    ${gettext("Create")}
                                </span>
                                <span slot="header">
                                    ${gettext(`Create ${type.name}`)}
                                </span>
                                <ak-proxy-form
                                    slot="form"
                                    type=${type.component}>
                                </ak-proxy-form>
                                <button slot="trigger" class="pf-c-dropdown__menu-item">
                                    ${type.name}<br>
                                    <small>${type.description}</small>
                                </button>
                            </ak-forms-modal>
                        </li>`;
                    });
                }), html`<ak-spinner></ak-spinner>`)}
            </ul>
        </ak-dropdown>
        ${super.renderToolbar()}`;
    }

    renderToolbarAfter(): TemplateResult {
        return html`<div class="pf-c-toolbar__group pf-m-filter-group">
            <div class="pf-c-toolbar__item pf-m-search-filter">
                <div class="pf-c-input-group">
                    <div class="pf-c-check">
                        <input class="pf-c-check__input" type="checkbox" id="hide-managed" name="hide-managed" ?checked=${this.hideManaged} @change=${() => {
                            this.hideManaged = !this.hideManaged;
                            this.page = 1;
                            this.fetch();
                        }} />
                        <label class="pf-c-check__label" for="hide-managed">${gettext("Hide managed mappings")}</label>
                    </div>
                </div>
            </div>
        </div>`;
    }
}
