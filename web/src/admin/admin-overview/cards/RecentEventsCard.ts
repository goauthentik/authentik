import "@goauthentik/admin/events/EventInfo";
import { ActionToLabel, EventGeo } from "@goauthentik/admin/events/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { truncate } from "@goauthentik/common/utils";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/Dropdown";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import { PaginatedResponse } from "@goauthentik/elements/table/Table";
import { Table, TableColumn } from "@goauthentik/elements/table/Table";

import { msg, str } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { Event, EventsApi } from "@goauthentik/api";

@customElement("ak-recent-events")
export class RecentEventsCard extends Table<Event> {
    @property()
    order = "-created";

    @property()
    pageSize = 10;

    async apiEndpoint(page: number): Promise<PaginatedResponse<Event>> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsList({
            ordering: this.order,
            page: page,
            pageSize: this.pageSize,
            search: this.search || "",
        });
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFCard,
            css`
                .pf-c-card__title {
                    --pf-c-card__title--FontFamily: var(
                        --pf-global--FontFamily--heading--sans-serif
                    );
                    --pf-c-card__title--FontSize: var(--pf-global--FontSize--md);
                    --pf-c-card__title--FontWeight: var(--pf-global--FontWeight--bold);
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
            new TableColumn(msg("Tenant"), "tenant_name"),
        ];
    }

    renderToolbar(): TemplateResult {
        return html`<div class="pf-c-card__title">
            <i class="pf-icon pf-icon-catalog"></i>&nbsp;${msg("Recent events")}
        </div>`;
    }

    row(item: EventWithContext): TemplateResult[] {
        return [
            html`<div><a href="${`#/events/log/${item.pk}`}">${ActionToLabel(item.action)}</a></div>
                <small>${item.app}</small>`,
            item.user?.username
                ? html`<div>
                          <a href="#/identity/users/${item.user.pk}"
                              >${truncate(item.user?.username, 15)}</a
                          >
                      </div>
                      ${item.user.on_behalf_of
                          ? html`<small>
                                <a href="#/identity/users/${item.user.on_behalf_of.pk}"
                                    >${msg(str`On behalf of ${item.user.on_behalf_of.username}`)}</a
                                >
                            </small>`
                          : html``}`
                : html`-`,
            html`<span>${item.created?.toLocaleString()}</span>`,
            html` <div>${item.clientIp || msg("-")}</div>
                <small>${EventGeo(item)}</small>`,
            html`<span>${item.tenant?.name || msg("-")}</span>`,
        ];
    }

    renderEmpty(): TemplateResult {
        return super.renderEmpty(html`<ak-empty-state header=${msg("No Events found.")}>
            <div slot="body">${msg("No matching events could be found.")}</div>
        </ak-empty-state>`);
    }
}
