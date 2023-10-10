import { DEFAULT_CONFIG } from "@goauthentik/app/common/api/config";
import { groupBy } from "@goauthentik/app/common/utils";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/app/elements/table/Table";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { ExtraUserObjectPermission, RbacApi } from "@goauthentik/api";

@customElement("ak-user-assigned-permissions-table")
export class UserAssignedPermissionsTable extends Table<ExtraUserObjectPermission> {
    @property()
    username?: string;

    apiEndpoint(page: number): Promise<PaginatedResponse<ExtraUserObjectPermission>> {
        return new RbacApi(DEFAULT_CONFIG).rbacPermissionsUsersList({
            username: this.username || "",
            page: page,
            ordering: this.order,
            search: this.search,
        });
    }

    groupBy(items: ExtraUserObjectPermission[]): [string, ExtraUserObjectPermission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabelVerbose;
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn("Model", "model"),
            new TableColumn("Permission", ""),
            new TableColumn(""),
        ];
    }

    row(item: ExtraUserObjectPermission): TemplateResult[] {
        return [
            html`${item.modelVerbose}`,
            html`${item.objectDescription || item.objectPk}`,
            html`✓`,
        ];
    }
}
