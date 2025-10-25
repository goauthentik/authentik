import "#elements/AppIcon";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { applicationListStyle } from "#admin/applications/ApplicationListPage";

import { Application, CoreApi, User } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-application-table")
export class UserApplicationTable extends Table<Application> {
    @property({ attribute: false })
    user?: User;

    static styles: CSSResult[] = [...super.styles, applicationListStyle];

    async apiEndpoint(): Promise<PaginatedResponse<Application>> {
        return new CoreApi(DEFAULT_CONFIG).coreApplicationsList({
            ...(await this.defaultEndpointConfig()),
            forUser: this.user?.pk,
        });
    }

    protected columns: TableColumn[] = [
        [""],
        [msg("Name"), "name"],
        [msg("Group"), "group"],
        [msg("Provider")],
        [msg("Provider Type")],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    row(item: Application): SlottedTemplateResult[] {
        return [
            html`<ak-app-icon name=${item.name} icon=${ifPresent(item.metaIcon)}></ak-app-icon>`,
            html`<a href="#/core/applications/${item.slug}">
                <div>${item.name}</div>
                ${item.metaPublisher ? html`<small>${item.metaPublisher}</small>` : nothing}
            </a>`,
            html`${item.group || msg("-")}`,
            item.provider
                ? html`<a href="#/core/providers/${item.providerObj?.pk}">
                      ${item.providerObj?.name}
                  </a>`
                : html`-`,
            html`${item.providerObj?.verboseName || msg("-")}`,
            html`<div>
                <ak-forms-modal>
                    <span slot="submit">${msg("Update")}</span>
                    <span slot="header">${msg("Update Application")}</span>
                    <ak-application-form slot="form" .instancePk=${item.slug}>
                    </ak-application-form>
                    <button slot="trigger" class="pf-c-button pf-m-plain">
                        <pf-tooltip position="top" content=${msg("Edit")}>
                            <i class="fas fa-edit" aria-hidden="true"></i>
                        </pf-tooltip>
                    </button>
                </ak-forms-modal>
                ${item.launchUrl
                    ? html`<a href=${item.launchUrl} target="_blank" class="pf-c-button pf-m-plain">
                          <pf-tooltip position="top" content=${msg("Open")}>
                              <i class="fas fa-share-square" aria-hidden="true"></i>
                          </pf-tooltip>
                      </a>`
                    : nothing}
            </div>`,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-application-table": UserApplicationTable;
    }
}
