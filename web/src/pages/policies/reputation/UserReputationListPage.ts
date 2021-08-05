import { t } from "@lingui/macro";
import { customElement, html, property, TemplateResult } from "lit-element";
import { AKResponse } from "../../../api/Client";
import { TablePage } from "../../../elements/table/TablePage";

import "../../../elements/buttons/ModalButton";
import "../../../elements/buttons/SpinnerButton";
import "../../../elements/forms/DeleteForm";
import "../../../elements/forms/ModalForm";
import { TableColumn } from "../../../elements/table/Table";
import { PAGE_SIZE } from "../../../constants";
import { UserReputation, PoliciesApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../../api/Config";

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

    apiEndpoint(page: number): Promise<AKResponse<UserReputation>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUsersList({
            ordering: this.order,
            page: page,
            pageSize: PAGE_SIZE,
            search: this.search || "",
        });
    }

    columns(): TableColumn[] {
        return [new TableColumn(t`Username`, "username"), new TableColumn(t`Score`, "score")];
    }

    renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length !== 1;
        const item = this.selectedElements[0];
        return html`<ak-forms-delete
            .obj=${item}
            objectLabel=${t`User Reputation`}
            .usedBy=${() => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUsersUsedByList({
                    id: item.pk,
                });
            }}
            .delete=${() => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUsersDestroy({
                    id: item.pk,
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${t`Delete`}
            </button>
        </ak-forms-delete>`;
    }

    row(item: UserReputation): TemplateResult[] {
        return [html`${item.username}`, html`${item.score}`];
    }
}
