import "#components/ak-event-info";
import "#elements/Tabs";
import "#elements/buttons/Dropdown";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { actionToLabel } from "#common/labels";

import { PaginatedResponse, Table, TableColumn, Timestamp } from "#elements/table/Table";
import { SlottedTemplateResult } from "#elements/types";

import { EventGeo, renderEventUser } from "#admin/events/utils";

import { Event, EventsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

@customElement("ak-recent-events")
export class RecentEventsCard extends Table<Event> {
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
        ...super.styles,
        PFCard,
        css`
            .pf-c-card__title {
                --pf-c-card__title--FontFamily: var(--pf-global--FontFamily--heading--sans-serif);
                --pf-c-card__title--FontSize: var(--pf-global--FontSize--md);
                --pf-c-card__title--FontWeight: var(--pf-global--FontWeight--bold);
            }
            * {
                word-break: break-all;
            }
        `,
    ];

    protected override rowLabel(item: Event): string {
        return actionToLabel(item.action);
    }

    protected columns: TableColumn[] = [
        [msg("Action"), "action"],
        [msg("User"), "user"],
        [msg("Creation Date"), "created"],
        [msg("Client IP"), "client_ip"],
        [msg("Brand"), "brand_name"],
    ];

    renderToolbar(): TemplateResult {
        return html`<div class="pf-c-card__title">
            <i class="pf-icon pf-icon-catalog" aria-hidden="true"></i>&nbsp;${msg("Recent events")}
        </div>`;
    }

    row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            html`<div><a href="${`#/events/log/${item.pk}`}">${actionToLabel(item.action)}</a></div>
                <small>${item.app}</small>`,
            renderEventUser(item),
            Timestamp(item.created),
            html` <div>${item.clientIp || msg("-")}</div>
                <small>${EventGeo(item)}</small>`,
            html`<span>${item.brand?.name || msg("-")}</span>`,
        ];
    }

    renderEmpty(inner?: SlottedTemplateResult): TemplateResult {
        if (this.error) {
            return super.renderEmpty(inner);
        }

        return super.renderEmpty(
            html`<ak-empty-state
                ><span>${msg("No Events found.")}</span>
                <div slot="body">${msg("No matching events could be found.")}</div>
            </ak-empty-state>`,
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-recent-events": RecentEventsCard;
    }
}
