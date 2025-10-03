import "#admin/rbac/ObjectPermissionModal";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";
import "#elements/forms/DeleteBulkForm";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { PaginatedResponse, TableColumn, Timestamp } from "#elements/table/Table";
import { TablePage } from "#elements/table/TablePage";
import { SlottedTemplateResult } from "#elements/types";

import {
    PoliciesApi,
    RbacPermissionsAssignedByRolesListModelEnum,
    Reputation,
} from "@goauthentik/api";

import getUnicodeFlagIcon from "country-flag-icons/unicode";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-policy-reputation-list")
export class ReputationListPage extends TablePage<Reputation> {
    protected override searchEnabled = true;
    public pageTitle = msg("Reputation scores");
    public pageDescription = msg(
        "Reputation for IP and user identifiers. Scores are decreased for each failed login and increased for each successful login.",
    );
    public pageIcon = "fa fa-ban";

    @property()
    order = "identifier";

    checkbox = true;
    clearOnRefresh = true;

    async apiEndpoint(): Promise<PaginatedResponse<Reputation>> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationScoresList({
            ...(await this.defaultEndpointConfig()),
        });
    }

    protected override rowLabel(item: Reputation): string | null {
        return item.identifier ?? null;
    }

    protected columns: TableColumn[] = [
        [msg("Identifier"), "identifier"],
        [msg("IP"), "ip"],
        [msg("Score"), "score"],
        [msg("Updated"), "updated"],
        [msg("Actions"), null, msg("Row Actions")],
    ];

    renderToolbarSelected(): TemplateResult {
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

    row(item: Reputation): SlottedTemplateResult[] {
        return [
            html`${item.identifier}`,
            html`${item.ipGeoData?.country
                ? html` ${getUnicodeFlagIcon(item.ipGeoData.country)} `
                : nothing}
            ${item.ip}`,
            html`${item.score}`,
            Timestamp(item.updated),
            html`
                <ak-rbac-object-permission-modal
                    model=${RbacPermissionsAssignedByRolesListModelEnum.AuthentikPoliciesReputationReputationpolicy}
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
