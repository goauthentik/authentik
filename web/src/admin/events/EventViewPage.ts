import "#components/ak-event-info";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EventWithContext } from "#common/events";
import { EventGeo, renderEventUser } from "#common/events/utils";
import { actionToLabel } from "#common/labels";

import { AKElement } from "#elements/Base";
import { Timestamp } from "#elements/table/shared";

import { setPageDetails } from "#components/ak-page-navbar";

import { EventsApi, EventToJSON } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, PropertyValues, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-event-view")
export class EventViewPage extends AKElement {
    @property({ type: String })
    eventID?: string;

    @state()
    event!: EventWithContext;

    static styles: CSSResult[] = [PFBase, PFGrid, PFDescriptionList, PFPage, PFContent, PFCard];

    fetchEvent(eventUuid: string) {
        new EventsApi(DEFAULT_CONFIG).eventsEventsRetrieve({ eventUuid }).then((ev) => {
            this.event = ev as EventWithContext;
        });
    }

    willUpdate(changedProperties: PropertyValues<this>) {
        if (changedProperties.has("eventID") && this.eventID) {
            this.fetchEvent(this.eventID);
        }
    }

    render(): TemplateResult {
        if (!this.event) {
            return html``;
        }
        return html` <section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <div class="pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-4-col-on-xl">
                    <div class="pf-c-card__title">${msg("Event info")}</div>
                    <div class="pf-c-card__body">
                        <dl class="pf-c-description-list pf-m-horizontal">
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Action")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${actionToLabel(this.event.action)}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("App")}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">${this.event.app}</div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("User")}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${renderEventUser(this.event)}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Created")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${Timestamp(this.event.created)}
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text"
                                        >${msg("Client IP")}</span
                                    >
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        <div>${this.event.clientIp || msg("-")}</div>
                                        <small>${EventGeo(this.event)}</small>
                                    </div>
                                </dd>
                            </div>
                            <div class="pf-c-description-list__group">
                                <dt class="pf-c-description-list__term">
                                    <span class="pf-c-description-list__text">${msg("Brand")}</span>
                                </dt>
                                <dd class="pf-c-description-list__description">
                                    <div class="pf-c-description-list__text">
                                        ${this.event.brand?.name || msg("-")}
                                    </div>
                                </dd>
                            </div>
                        </dl>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-8-col-on-xl">
                    <ak-event-info .event=${this.event}></ak-event-info>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">${msg("Raw event info")}</div>
                    <div class="pf-c-card__body">
                        <pre>${JSON.stringify(EventToJSON(this.event), null, 4)}</pre>
                    </div>
                </div>
            </div>
        </section>`;
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);
        setPageDetails({
            icon: "pf-icon pf-icon-catalog",
            header: this.event ? msg(str`Event ${this.event.pk}`) : msg("Loading..."),
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-view": EventViewPage;
    }
}
