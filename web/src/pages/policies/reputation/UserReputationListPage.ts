import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import { PoliciesApi, UserReputation } from "@goauthentik/api";

import { AKResponse } from "../../../api/Client";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { uiConfig } from "../../../common/config";
import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteBulkForm";
import "../../../elements/forms/ModalForm";
import { TableColumn } from "../../../elements/table/Table";
import { TablePage } from "../../../elements/table/TablePage";

@customElement("ak-policy-reputation-user-list")
export class UserReputationListPage extends TablePage<UserReputation> {
    searchEnabled(): boolean {
        return true;
    }
    pageTitle(): string {
        return t`User Reputation`;
    }
    pageDescription(): string {
        return t`Reputation for usernames. Scores are decreased for each failed login and increased for each successful login.`;
    }
    pageIcon(): string {
        return "fa fa-ban";
    }

    checkbox = true;

    @property()
    order = "username";

    async apiEndpoint(page: number): Promise<AKResponse<UserReputation>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUsersList({
            ordering: this.order,
            page: page,
            pageSize: (await uiConfig()).pagination.perPage,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(t`Username`, "username"), new TableColumn(t`Score`, "score")];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${t`User Reputation`}
            .objects=${this.selectedElements}
            .usedBy=${(item: UserReputation) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUsersUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${(item: UserReputation) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUsersDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete-bulk>`;
    }

    row(item: UserReputation): TemplateResult[] {
        return [html`${item.username}`, html`${item.score}`];
    }
}
