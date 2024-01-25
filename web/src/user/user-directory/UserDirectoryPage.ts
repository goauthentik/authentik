import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { uiConfig } from "@goauthentik/common/ui/config";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { TableColumn } from "@goauthentik/elements/table/Table";
import { TablePage } from "@goauthentik/elements/table/TablePage";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAlert from "@patternfly/patternfly/components/Alert/alert.css";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

import { CoreApi, UserDirectory } from "@goauthentik/api";

const knownFields = {
    avatar: "",
    username: msg("Username"),
    name: msg("Name"),
    email: msg("Email"),
};

@customElement("ak-user-directory")
export class UserDirectoryPage extends TablePage<UserDirectory> {
    expandable = true;

    searchEnabled(): boolean {
        return true;
    }

    @property()
    order = "username";

    @state()
    fields?: string[];

    @state()
    attributes?: object[];

    static get styles(): CSSResult[] {
        return [...super.styles, PFDescriptionList, PFCard, PFAlert, PFAvatar];
    }

    async apiEndpoint(page: number): Promise<PaginatedResponse<UserDirectory>> {
        const fields = await new CoreApi(DEFAULT_CONFIG).coreUserDirectoryFieldsRetrieve();
        this.fields = fields.fields;
        this.attributes = fields.attributes;
        return await new CoreApi(DEFAULT_CONFIG).coreUserDirectoryList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        if (this.fields === undefined) return [];
        return this.fields
            .filter((item) => item in knownFields)
            .map((item) =>
                item === "avatar"
                    ? new TableColumn(knownFields[item])
                    : new TableColumn(knownFields[item], item),
            );
    }

    row(item): TemplateResult[] {
        if (this.fields === undefined) return [];
        return this.fields
            .filter((field: string) => knownFields.hasOwnProperty(field))
            .map((field: string) =>
                field !== "avatar"
                    ? html`${item.userFields[field]}`
                    : html` <img
                          class="pf-c-avatar"
                          src=${item.userFields[field]}
                          alt="${msg("Avatar image")}"
                      />`,
            );
    }

    renderExpanded(item: UserDirectory): TemplateResult {
        return html`<td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                <dl class="pf-c-description-list pf-m-horizontal">
                    ${this.fields.includes("groups")
                        ? html`
                              <div class="pf-c-description-list__group">
                                  <dt class="pf-c-description-list__term">
                                      <span class="pf-c-description-list__text"
                                          >${msg("Groups")}</span
                                      >
                                  </dt>
                                  <dd class="pf-c-description-list__description">
                                      ${item.userFields["groups"].map(
                                          (group: string) => html`
                                              <div class="pf-c-description-list__text">
                                                  ${group}
                                              </div>
                                          `,
                                      )}
                                  </dd>
                              </div>
                          `
                        : html``}
                    ${this.attributes.map((attr: any) =>
                        item.attributes[attr.attribute] !== null
                            ? html`
                                  <div class="pf-c-description-list__group">
                                      <dt class="pf-c-description-list__term">
                                          <span class="pf-c-description-list__text"
                                              >${attr.display_name}</span
                                          >
                                      </dt>
                                      <dd class="pf-c-description-list__description">
                                          <div class="pf-c-description-list__text">
                                              ${item.attributes[attr.attribute]}
                                          </div>
                                      </dd>
                                  </div>
                              `
                            : html``,
                    )}
                </dl>
            </div>
        </td>`;
    }

    renderPageHeader(): TemplateResult {
        return html`
            <div class="bar">
                <section class="pf-c-page__main-section pf-m-light">
                    <div class="pf-c-content">
                        <h1>
                            <i class="pf-icon pf-icon-project"></i>
                            ${msg("User directory")}
                        </h1>
                    </div>
                </section>
            </div>
        `;
    }
}
