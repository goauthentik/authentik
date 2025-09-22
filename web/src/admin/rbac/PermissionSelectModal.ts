import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TableModal } from "#elements/table/TableModal";
import { SlottedTemplateResult } from "#elements/types";

import { Permission, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-rbac-permission-select-table")
export class PermissionSelectModal extends TableModal<Permission> {
    checkbox = true;
    checkboxChip = true;

    protected override searchEnabled = true;

    @property()
    confirm!: (selectedItems: Permission[]) => Promise<unknown>;

    order = "content_type__app_label,content_type__model";

    static styles: CSSResult[] = [...super.styles, PFBanner];

    async apiEndpoint(): Promise<PaginatedResponse<Permission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsList(await this.defaultEndpointConfig());
    }

    groupBy(items: Permission[]): [string, Permission[]][] {
        return groupBy(items, (perm) => {
            return perm.appLabelVerbose;
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "codename"],
        [msg("Model"), ""],
    ];

    row(item: Permission): SlottedTemplateResult[] {
        return [
            html`<div>
                <div>${item.name}</div>
            </div>`,
            html`${item.modelVerbose}`,
        ];
    }

    renderSelectedChip(item: Permission): TemplateResult {
        return html`${item.name}`;
    }

    renderModalInner(): TemplateResult {
        return html`<section class="pf-c-modal-box__header pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1 class="pf-c-title pf-m-2xl">${msg("Select permissions to assign")}</h1>
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-permission-select-table": PermissionSelectModal;
    }
}
