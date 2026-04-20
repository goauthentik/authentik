import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, Group } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-user-group-table")
export class UserGroupTable extends Table<Group> {
    public static styles: CSSResult[] = [...super.styles, PFBanner];

    public override checkbox = true;
    public override checkboxChip = true;

    protected override searchEnabled = true;
    public override supportsQL = true;

    public override order = "name";

    protected override async apiEndpoint(): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ...(await this.defaultEndpointConfig()),
            includeUsers: false,
        });
    }

    protected override columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Superuser"), "is_superuser"],
        [msg("Members"), ""],
    ];

    protected override row(item: Group): SlottedTemplateResult[] {
        return [
            item.name,
            html`<ak-status-label type="neutral" ?good=${item.isSuperuser}></ak-status-label>`,
            item.users?.length || 0,
        ];
    }

    protected override renderSelectedChip(item: Group): SlottedTemplateResult {
        return item.name;
    }

    protected override render(): SlottedTemplateResult {
        const willSuperuser = this.selectedElements.some((g) => g.isSuperuser);

        if (!willSuperuser) {
            return super.render();
        }

        return html`<div class="pf-c-banner pf-m-warning">
                ${msg(
                    "Warning: Adding the user to the selected group(s) will give them superuser permissions.",
                )}
            </div>
            ${super.render()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-group-table": UserGroupTable;
    }
}
