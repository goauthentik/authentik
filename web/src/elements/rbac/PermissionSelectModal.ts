import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/elements/buttons/SpinnerButton";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TableModal } from "@goauthentik/elements/table/TableModal";



import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";



import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";



import { CoreApi, Permission } from "@goauthentik/api";
import { groupBy } from "@goauthentik/app/common/utils";


@customElement("ak-rbac-permission-select-table")
export class PermissionSelectModal extends TableModal<Permission> {
    checkbox = true;
    checkboxChip = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    confirm!: (selectedItems: Permission[]) => Promise<unknown>;

    order = "content_type__app_label,codename";

    static get styles(): CSSResult[] {
        return super.styles.concat(PFBanner);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<Permission>> {
        return new CoreApi(DEFAULT_CONFIG).coreRbacPermissionsList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    groupBy(items: Permission[]): [string, Permission[]][] {
        return groupBy(items, (perm => {
            return perm.appLabel;
        }));
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Name"), "username"),
            new TableColumn(msg("Superuser"), "is_superuser"),
            new TableColumn(msg("Members"), ""),
        ];
    }

    row(item: Permission): TemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
            </div>`,
            html``,
        ];
    }

    renderSelectedChip(item: Permission): TemplateResult {
        return html`${item.name}`;
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${msg("Select permissions to grant")}</h1>
                </div>
            </section>
            <section class="pf-c-modal-box__body pf-m-light">${this.renderTable()}</section>
            <footer class="pf-c-modal-box__footer">
                <ak-spinner-button
                    .callAction=${() => {
                        return this.confirm(this.selectedElements).then(() => {
                            this.open = false;
                        });
                    }}
                    class="pf-m-primary"
                >
                    ${msg("Add")} </ak-spinner-button
                >&nbsp;
                <ak-spinner-button
                    .callAction=${async () => {
                        this.open = false;
                    }}
                    class="pf-m-secondary"
                >
                    ${msg("Cancel")}
                </ak-spinner-button>
            </footer>`;
    }
}
