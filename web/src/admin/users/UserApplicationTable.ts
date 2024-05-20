import { applicationListStyle } from "@goauthentik/admin/applications/ApplicationListPage";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { PFSize } from "@goauthentik/common/enums.js";
import { uiConfig } from "@goauthentik/common/ui/config";
import "@goauthentik/components/ak-app-icon";
import { PaginatedResponse, Table, TableColumn } from "@goauthentik/elements/table/Table";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Application, CoreApi, User } from "@goauthentik/api";

@customElement("ak-user-application-table")
export class UserApplicationTable extends Table<Application> {
    @property({ attribute: false })
    user?: User;

    static get styles(): CSSResult[] {
        return super.styles.concat(applicationListStyle);
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<Application>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            forUser: this.user?.pk,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            ordering: this.order,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(""),
            new TableColumn(msg("Name"), "name"),
            new TableColumn(msg("Group"), "group"),
            new TableColumn(msg("Provider")),
            new TableColumn(msg("Provider Type")),
            new TableColumn(msg("Actions")),
        ];
    }

    row(item: Application): TemplateResult[] {
        return [
            html`<ak-app-icon size=${PFSize.Medium} .app=${item}></ak-app-icon>`,
            html`<a href="#/core/applications/${item.slug}">
                <div>${item.name}</div>
                ${item.metaPublisher ? html`<small>${item.metaPublisher}</small>` : html``}
            </a>`,
            html`${item.group || msg("-")}`,
            item.provider
                ? html`<a href="#/core/providers/${item.providerObj?.pk}">
                      ${item.providerObj?.name}
                  </a>`
                : html`-`,
            html`${item.providerObj?.verboseName || msg("-")}`,
            html`<ak-forms-modal>
                    <span slot="submit"> ${msg("Update")} </span>
                    <span slot="header"> ${msg("Update Application")} </span>
                    <ak-application-form slot="form" .instancePk=${item.slug}>
                    </ak-application-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                ${item.launchUrl
                    ? html`<a href=${item.launchUrl} target="_blank" class="pf-c-button pf-m-plain">
                          <pf-tooltip position="top" content=${msg("Open")}>
                              <i class="fas fa-share-square"></i>
                          </pf-tooltip>
                      </a>`
                    : html``}`,
        ];
    }
}
