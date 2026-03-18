import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Permission, RbacApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-rbac-permission-select-form")
export class PermissionSelectForm extends Table<Permission> {
    public override checkbox = true;
    public override checkboxChip = true;

    protected override searchEnabled = true;

    public override order = "content_type__app_label,content_type__model";

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

    protected row(item: Permission): SlottedTemplateResult[] {
        return [html`<div>${item.name}</div>`, html`${item.modelVerbose}`];
    }

    protected renderSelectedChip(item: Permission): SlottedTemplateResult {
        return item.name;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-rbac-permission-select-form": PermissionSelectForm;
    }
}
