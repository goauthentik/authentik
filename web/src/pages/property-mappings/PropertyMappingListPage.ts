import { gettext } from "django";
import { customElement, html, property, TemplateResult } from "lit-element";
import { PropertyMapping } from "../../api/PropertyMapping";
import { AKResponse } from "../../api/Client";
import { TablePage } from "../../elements/table/TablePage";

import "../../elements/buttons/ModalButton";
import "../../elements/buttons/Dropdown";
import "../../elements/buttons/SpinnerButton";
import { TableColumn } from "../../elements/table/Table";

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
        return gettext("pf-icon pf-icon-blueprint");
    }

    @property()
    order = "name";

    @property({type: Boolean})
    hideManaged = false;

    apiEndpoint(page: number): Promise<AKResponse<PropertyMapping>> {
        return PropertyMapping.list({
            ordering: this.order,
            page: page,
            search: this.search || "",
            managed__isnull: this.hideManaged,
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
            html`${item.verbose_name}`,
            html`
            <ak-modal-button href="${PropertyMapping.adminUrl(`${item.pk}/update/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Edit")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${PropertyMapping.adminUrl(`${item.pk}/test/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-secondary">
                    ${gettext("Test")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            <ak-modal-button href="${PropertyMapping.adminUrl(`${item.pk}/delete/`)}">
                <ak-spinner-button slot="trigger" class="pf-m-danger">
                    ${gettext("Delete")}
                </ak-spinner-button>
                <div slot="modal"></div>
            </ak-modal-button>
            `,
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
                <li>
                    <ak-modal-button href="${PropertyMapping.adminUrl("create/?type=LDAPPropertyMapping")}">
                        <button slot="trigger" class="pf-c-dropdown__menu-item">${gettext("LDAP Property Mapping")}<br>
                            <small>
                                ${gettext("Map LDAP Property to User or Group object attribute")}
                            </small>
                        </button>
                        <div slot="modal"></div>
                    </ak-modal-button>
                </li>
                <li>
                    <ak-modal-button href="${PropertyMapping.adminUrl("create/?type=SAMLPropertyMapping")}">
                        <button slot="trigger" class="pf-c-dropdown__menu-item">${gettext("SAML Property Mapping")}<br>
                            <small>
                                ${gettext("Map User/Group attribute to SAML Attribute, which can be used by the Service Provider.")}
                            </small>
                        </button>
                        <div slot="modal"></div>
                    </ak-modal-button>
                </li>
                <li>
                    <ak-modal-button href="${PropertyMapping.adminUrl("create/?type=ScopeMapping")}">
                        <button slot="trigger" class="pf-c-dropdown__menu-item">${gettext("Scope Mapping")}<br>
                            <small>
                                ${gettext("Map an OAuth Scope to users properties")}
                            </small>
                        </button>
                        <div slot="modal"></div>
                    </ak-modal-button>
                </li>
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
                            this.fetch();
                        }} />
                        <label class="pf-c-check__label" for="hide-managed">${gettext("Hide managed mappings")}</label>
                    </div>
                </div>
            </div>
        </div>`;
    }
}
