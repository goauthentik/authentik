import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { renderDescriptionList } from "@goauthentik/components/DescriptionList.js";
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

type UserFieldAttributes = { display_name: string; attribute: string };

@customElement("ak-user-directory")
export class UserDirectoryPage extends TablePage<UserDirectory> {
    expandable = true;

    searchEnabled(): boolean {
        return true;
    }

    pageTitle(): string {
        return msg("User Directory");
    }

    pageDescription(): string {
        return msg("Display a list of users on this system.");
    }

    pageIcon(): string {
        return "fa fa-user";
    }

    @property()
    order = "username";

    @state()
    fields?: string[];

    @state()
    userFieldAttributes?: object[] = [];

    static get styles(): CSSResult[] {
        return [...super.styles, PFDescriptionList, PFCard, PFAlert, PFAvatar];
    }

    async apiEndpoint(): Promise<PaginatedResponse<UserDirectory>> {
        const fields = await new CoreApi(DEFAULT_CONFIG).coreUserDirectoryFieldsRetrieve();
        this.fields = fields.fields;
        this.userFieldAttributes = fields.attributes;
        return await new CoreApi(DEFAULT_CONFIG).coreUserDirectoryList(
            await this.defaultEndpointConfig(),
        );
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
        const groupDescription = this.fields?.includes("groups")
            ? [
                  [msg("Groups")],
                  item.userFields["groups"].map(
                      (group: string) => html`
                          <div class="pf-c-description-list__text">${group}</div>
                      `,
                  ),
              ]
            : [];

        const userDescriptions = ((this.userFieldAttributes ?? []) as UserFieldAttributes[])
            .filter(({ attribute }) => attribute !== null)
            .map(({ display_name, attribute }) => [display_name, item.attributes[attribute]]);

        return html`<td role="cell" colspan="3">
            <div class="pf-c-table__expandable-row-content">
                ${renderDescriptionList([...groupDescription, ...userDescriptions])}
            </div>
        </td>`;
    }
}
