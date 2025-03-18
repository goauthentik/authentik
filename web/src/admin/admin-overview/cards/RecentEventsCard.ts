import { EventUser, formatGeoEvent } from "@goauthentik/admin/events/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { actionToLabel } from "@goauthentik/common/labels";
import { getRelativeTime } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-event-info";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/Dropdown";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";
import { SlottedTemplateResult } from "@goauthentik/elements/types";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { Event, EventsApi } from "@goauthentik/api";

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

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFCard,
            css`
                .pf-c-table__sort.pf-m-selected {
                    background-color: var(--pf-global--BackgroundColor--dark-400);
                    border-block-end: var(--pf-global--BorderWidth--xl) solid var(--ak-accent);

                    .pf-c-table__button {
                        --pf-c-table__sort__button__text--Color: var(--ak-accent);
                        color: var(--pf-c-nav__link--m-current--Color);

                        .pf-c-table__text {
                            --pf-c-table__sort__button__text--Color: var(
                                --pf-c-nav__link--m-current--Color
                            );
                        }
                    }
                }

                .pf-c-card__title {
                    --pf-c-card__title--FontFamily: var(
                        --pf-global--FontFamily--heading--sans-serif
                    );
                    --pf-c-card__title--FontSize: var(--pf-global--FontSize--md);
                    --pf-c-card__title--FontWeight: var(--pf-global--FontWeight--bold);
                }

                td[role="cell"] .ip-address {
                    max-width: 18ch;
                    text-overflow: ellipsis;
                    overflow: hidden;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                }

                th[role="columnheader"]:nth-child(3) {
                    --pf-c-table--cell--MinWidth: fit-content;
                    --pf-c-table--cell--MaxWidth: none;
                    --pf-c-table--cell--Width: 1%;
                    --pf-c-table--cell--Overflow: visible;
                    --pf-c-table--cell--TextOverflow: clip;
                    --pf-c-table--cell--WhiteSpace: nowrap;
                }

                .group-header {
                    display: grid;
                    grid-template-columns: 1fr auto;
                    gap: var(--pf-global--spacer--sm);
                    font-weight: var(--pf-global--FontWeight--bold);
                    font-size: var(--pf-global--FontSize--md);
                    font-variant: all-petite-caps;
                }

                .pf-c-table thead:not(:first-child) {
                    background: hsl(0deg 0% 0% / 10%);

                    > tr {
                        border-block-end: 2px solid
                            var(
                                --pf-c-page__header-tools--c-button--m-selected--before--BackgroundColor
                            );
                        font-family: var(--pf-global--FontFamily--heading--sans-serif);
                    }
                }

                tbody * {
                    word-break: break-all;
                }
            `,
        );
    }

    columns(): TableColumn[] {
        return [
            new TableColumn(msg("Action"), "action"),
            new TableColumn(msg("User"), "user"),
            new TableColumn(msg("Creation Date"), "created"),
            new TableColumn(msg("Client IP"), "client_ip"),
            new TableColumn(msg("Brand"), "brand_name"),
        ];
    }

    renderToolbar(): TemplateResult {
        return html`<div class="pf-c-card__title">
            <i class="pf-icon pf-icon-catalog"></i>&nbsp;${msg("Recent events")}
        </div>`;
    }

    override groupBy(items: Event[]): [SlottedTemplateResult, Event[]][] {
        const groupedByDay = new Map<string, Event[]>();

        for (const item of items) {
            const day = new Date(item.created);
            day.setHours(0, 0, 0, 0);
            const serializedDay = day.toISOString();

            let dayEvents = groupedByDay.get(serializedDay);
            if (!dayEvents) {
                dayEvents = [];
                groupedByDay.set(serializedDay, dayEvents);
            }

            dayEvents.push(item);
        }

        return Array.from(groupedByDay, ([serializedDay, events]) => {
            const day = new Date(serializedDay);
            return [
                html` <div class="pf-c-content group-header">
                    <div>${getRelativeTime(day)}</div>
                    <small>${day.toLocaleDateString()}</small>
                </div>`,
                events,
            ];
        });
    }

    row(item: EventWithContext): SlottedTemplateResult[] {
        return [
            html`<div><a href="${`#/events/log/${item.pk}`}">${actionToLabel(item.action)}</a></div>
                <small class="pf-m-monospace">${item.app}</small>`,
            EventUser(item),

            html`<time datetime="${item.created.toISOString()}" class="pf-c-content">
                <div><small>${item.created.toLocaleTimeString()}</small></div>
            </time>`,

            html`<div class="ip-address pf-m-monospace">${item.clientIp || msg("-")}</div>
                <small class="geographic-location">${formatGeoEvent(item)}</small>`,

            html`<span>${item.brand?.name || msg("-")}</span>`,
        ];
    }

    renderEmpty(inner?: SlottedTemplateResult): TemplateResult {
        if (this.error) {
            return super.renderEmpty(inner);
        }

        return super.renderEmpty(
            html`<ak-empty-state header=${msg("No Events found.")}>
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
