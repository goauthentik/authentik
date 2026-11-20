import "#elements/Spinner";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import "#elements/EmptyState";

import { aki } from "#common/api/client";
import { createPaginatedResponse } from "#common/api/responses";

import { PaginatedResponse, RowType, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import Styles from "#admin/admin-overview/cards/RecentEventsCard.css";

import { EventsApi, EventTopPerUser } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-top-applications-table")
export class TopApplicationsTable extends Table<EventTopPerUser> {
    static styles: CSSResult[] = [
        // ---
        ...super.styles,
        PFCard,
        Styles,
    ];

    protected async apiEndpoint(): Promise<PaginatedResponse<EventTopPerUser, object>> {
        const data = await aki(EventsApi).eventsEventsTopPerUserList({
            action: "authorize_application",
            topN: 11,
        });

        return createPaginatedResponse(data);
    }

    protected columns: TableColumn[] = [[msg("Application")], [msg("Logins")], [""]];

    protected row(item: EventTopPerUser): RowType[] {
        return [
            html`${item.application.name}`,
            html`${item.countedEvents}`,
            html`<progress
                value="${item.countedEvents}"
                max="${this.data ? this.data.results[0].countedEvents : 0}"
            ></progress>`,
        ];
    }

    protected override renderEmpty(): SlottedTemplateResult {
        return super.renderEmpty(
            html`<ak-empty-state>
                <span>${msg("No data yet.")}</span>
            </ak-empty-state>`,
        );
    }

    protected renderToolbar(): SlottedTemplateResult {
        return html`<h1 class="pf-c-card__title">
            <i class="pf-icon pf-icon-server" aria-hidden="true"></i>
            ${msg("Apps with most usage")}
        </h1>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-top-applications-table": TopApplicationsTable;
    }
}
