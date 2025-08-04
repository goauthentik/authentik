import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";
import { formatElapsedTime } from "#common/temporal";

import { PaginatedResponse, TableColumn } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";

import {
    PoliciesApi,
    RbacPermissionsAssignedByUsersListModelEnum,
    Reputation,
} from "@goauthentik/api";

import getUnicodeFlagIcon from "country-flag-icons/unicode";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-policy-reputation-list")
export class ReputationListPage extends TablePage<Reputation> {
    protected override searchEnabled(): boolean {
        return true;
    }

    protected pageTitle(): string {
        return msg("Reputation scores");
    }

    protected pageDescription(): string {
        return msg(
            "Reputation for IP and user identifiers. Scores are decreased for each failed login and increased for each successful login.",
        );
    }

    protected pageIcon(): string {
        return "fa fa-ban";
    }

    @property()
    public override order = "identifier";

    public override checkbox = true;
    public override clearOnRefresh = true;

    protected async apiEndpoint(): Promise<PaginatedResponse<Reputation>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationScoresList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected columns(): TableColumn[] {
        return [
            new TableColumn(msg("Identifier"), "identifier"),
            new TableColumn(msg("IP"), "ip"),
            new TableColumn(msg("Score"), "score"),
            new TableColumn(msg("Updated"), "updated"),
            new TableColumn(msg("Actions")),
        ];
    }

    protected override renderToolbarSelected(): TemplateResult {
        const disabled = this.selectedElements.length < 1;
        return html`<ak-forms-delete-bulk
            objectLabel=${msg("Reputation")}
            .objects=${this.selectedElements}
            .usedBy=${(item: Reputation) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationScoresUsedByList({
                    reputationUuid: item.pk || "",
                });
            }}
            .delete=${(item: Reputation) => {
                return new PoliciesApi(DEFAULT_CONFIG).policiesReputationScoresDestroy({
                    reputationUuid: item.pk || "",
                });
            }}
        >
            <button ?disabled=${disabled} slot="trigger" class="pf-c-button pf-m-danger">
                ${msg("Delete")}
            </button>
        </ak-forms-delete-bulk>`;
    }

    protected row(item: Reputation): TemplateResult[] {
        return [
            html`${item.identifier}`,
            html`${item.ipGeoData?.country
                ? html` ${getUnicodeFlagIcon(item.ipGeoData.country)} `
                : html``}
            ${item.ip}`,
            html`${item.score}`,
            html`<div>${formatElapsedTime(item.updated)}</div>
                <small>${item.updated.toLocaleString()}</small>`,
            html`
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByUsersListModelEnum.AuthentikPoliciesReputationReputationpolicy}
                    objectPk=${item.pk || ""}
                >
                </ak-rbac-object-permission-modal>
            `,
        ];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-reputation-list": ReputationListPage;
    }
}
