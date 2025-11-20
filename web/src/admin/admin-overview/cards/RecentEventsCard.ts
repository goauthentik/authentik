import "#components/ak-event-info";
import "#elements/Tabs";
import "#elements/timestamp/ak-timestamp";
import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { EntityLabel } from "#common/i18n/nouns";
import { actionToLabel } from "#common/labels";

import { PaginatedResponse, Table, TableColumn } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import Styles from "#admin/admin-overview/cards/RecentEventsCard.css";
import { EventGeo, renderEventUser } from "#admin/events/utils";

import { Event, EventsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

@customElement("ak-recent-events")
export class RecentEventsCard extends Table<Event> {
    public override role = "region";
    public override ariaLabel = msg("Recent events", { id: "aria.label.recent-events" });
    public override label = msg("Events", { id: "card.label.recent-events" });

    protected override entityLabel: EntityLabel = {
        singular: msg("Event", { id: "entity.event.singular" }),
        plural: msg("Events", { id: "entity.event.plural" }),
    };

    @property()
    order = "-created";

    @property({ type: Number })
    pageSize = 10;

    async apiEndpoint(): Promise<PaginatedResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            ...(await this.defaultEndpointConfig()),
            pageSize: this.pageSize,
        });
    }

    static styles: CSSResult[] = [
        // ---
        ...super.styles,
        PFCard,
        Styles,
    ];

    protected override rowLabel(item: Event): string {
        return actionToLabel(item.action);
    }

    protected columns: TableColumn[] = [
        [msg("Action", { id: "column.action" }), "action"],
        [msg("User", { id: "column.user" }), "user"],
        [msg("Creation Date", { id: "column.creation-date" }), "created"],
        [msg("Client IP", { id: "column.client-ip" }), "client_ip"],
    ];

    renderToolbar(): TemplateResult {
        return html`<h1 class="pf-c-card__title">
            <i class="pf-icon pf-icon-catalog" aria-hidden="true"></i>
            ${msg("Recent events")}
        </h1>`;
    }

    row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            html`<div><a href="${`#/events/log/${item.pk}`}">${actionToLabel(item.action)}</a></div>
                <small>${item.app}</small>`,
            renderEventUser(item),
            html`<ak-timestamp .timestamp=${item.created}></ak-timestamp>`,
            html` <div>${item.clientIp || msg("-")}</div>
                <small>${EventGeo(item)}</small>`,
        ];
    }

    renderEmpty(inner?: SlottedTemplateResult): TemplateResult {
        if (this.error) {
            return super.renderEmpty(inner);
        }

        const entityLabel = this.entityLabel.plural.toLowerCase();

        return super.renderEmpty(
            html`<ak-empty-state
                ><span
                    >${msg(str`No ${entityLabel} found.`, {
                        id: "empty-state.heading",
                    })}</span
                >
                <div slot="body">
                    ${msg(str`No matching ${entityLabel} could be found.`, {
                        id: "empty-state.body",
                    })}
                </div>
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-recent-events": RecentEventsCard;
    }
}
