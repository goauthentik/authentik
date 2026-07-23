import { aki } from "#common/api/client";

import { AKModal } from "#elements/dialogs/ak-modal";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { Application, CoreApi, RequestableTarget, RequestsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-request-entitlement-modal")
export class RequestEntitlementModal extends Table<RequestableTarget> {
    protected override searchEnabled = true;

    public override searchPlaceholder = msg("Search for an entitlement...", {
        id: "requests.browse.entitlement-modal.search-placeholder",
    });
    public override emptyStateMessage = msg("No entitlements found for this application.", {
        id: "requests.browse.entitlement-modal.empty-state",
    });
    public override rowClassNames = "pf-m-hoverable";
    public cancelable = true;

    @property({ attribute: false })
    public app: Application | null = null;

    public renderHeader(): SlottedTemplateResult {
        return html`<h1 part="form-header" class="pf-c-title pf-m-2xl">
            ${msg("Select entitlement", { id: "requests.browse.entitlement-modal.header" })}
        </h1>`;
    }

    protected override rowClickListener(item: RequestableTarget): void {
        this.#requestAccess(item.pbmUuid);
    }

    async #requestAccess(pbmUuid: string): Promise<void> {
        try {
            const { link } = await aki(RequestsApi).requestsGrantRequestsCreate({
                grantRequestCreateRequest: { pbms: [pbmUuid] },
            });
            window.location.assign(link);
        } catch (error) {
            showAPIErrorMessage(error);
        }
    }

    protected override async apiEndpoint(): Promise<PaginatedResponse<RequestableTarget>> {
        const entitlements = await aki(CoreApi).coreApplicationEntitlementsRequestableList({
            ...(await this.defaultEndpointConfig()),
            app: this.app?.pk,
        });

        if (entitlements.pagination.count === 1) {
            this.rowClickListener(entitlements.results[0]);

            if (this.parentElement instanceof AKModal) {
                this.parentElement.close();
            }
        }
        return entitlements;
    }

    protected columns: TableColumn[] = [
        [msg("Entitlement", { id: "requests.browse.entitlement-modal.column.entitlement" })],
    ];

    protected override row(item: RequestableTarget): SlottedTemplateResult[] {
        return [item.label];
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-request-entitlement-modal": RequestEntitlementModal;
    }
}
