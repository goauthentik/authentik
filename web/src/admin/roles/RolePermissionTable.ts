import { DEFAULT_CONFIG } from "@goauthentik/app/common/api/config";
import { groupBy } from "@goauthentik/app/common/utils";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/app/elements/table/Table";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { CoreApi, Permission } from "@goauthentik/api";

@customElement("ak-role-permissions")
export class RolePermissionTable extends Table<Permission> {
    @property()
    roleUuid?: string;

    apiEndpoint(page: number): Promise<PaginatedResponse<Permission>> {
        return new CoreApi(DEFAULT_CONFIG).coreRbacPermissionsList({
            role: this.roleUuid,
            page: page,
        });
    }

    public groupBy(items: Permission[]): [string, Permission[]][] {
        return groupBy(items, (obj) => {
            return obj.appLabel;
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn("Permission", "")];
    }

    row(item: Permission): TemplateResult[] {
        return [html`${item.codename}`];
    }
}
