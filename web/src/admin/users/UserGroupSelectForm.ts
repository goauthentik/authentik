import "#components/ak-status-label";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, Group } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

@customElement("ak-user-group-select-form")
export class UserGroupSelectForm extends Table<Group> {
    public static styles: CSSResult[] = [...super.styles, PFBanner];

    public override checkbox = true;
    public override checkboxChip = true;

    protected override searchEnabled = true;
    public override supportsQL = true;

    public override order = "name";

    protected async apiEndpoint(): Promise<PaginatedResponse<Group>> {
        return new CoreApi(DEFAULT_CONFIG).coreGroupsList({
            ...(await this.defaultEndpointConfig()),
            includeUsers: false,
        });
    }

    protected columns: TableColumn[] = [
        [msg("Name"), "username"],
        [msg("Superuser"), "is_superuser"],
        [msg("Members"), ""],
    ];

    protected row(item: Group): SlottedTemplateResult[] {
        return [
            html`<div>${item.name}</div>`,
            html`<ak-status-label type="neutral" ?good=${item.isSuperuser}></ak-status-label>`,
            html`${(item.users || []).length}`,
        ];
    }

    protected renderSelectedChip(item: Group): SlottedTemplateResult {
        return item.name;
    }

    protected override render(): SlottedTemplateResult {
        const willSuperuser = this.selectedElements.filter((g) => g.isSuperuser).length;

        return html`${willSuperuser
            ? html`
                  <div class="pf-c-banner pf-m-warning">
                      ${msg(
                          "Warning: Adding the user to the selected group(s) will give them superuser permissions.",
                      )}
                  </div>
              `
            : nothing}
        ${super.render()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-group-select-form": UserGroupSelectForm;
    }
}
