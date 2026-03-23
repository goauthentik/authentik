import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { RbacApi, Role } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-role-select-form")
export class UserRoleSelectForm extends Table<Role> {
    public override checkbox = true;
    public override checkboxChip = true;

    protected override searchEnabled = true;
    public override supportsQL = true;

    public override order = "name";

    protected async apiEndpoint(): Promise<PaginatedResponse<Role>> {
        return new RbacApi(DEFAULT_CONFIG).rbacRolesList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected columns: TableColumn[] = [[msg("Name"), "name"]];

    protected row(item: Role): SlottedTemplateResult[] {
        return [html`<div>${item.name}</div>`];
    }

    protected renderSelectedChip(item: Role): SlottedTemplateResult {
        return item.name;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-role-select-form": UserRoleSelectForm;
    }
}
