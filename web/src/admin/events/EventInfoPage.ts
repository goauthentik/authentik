import "@goauthentik/admin/events/EventInfo";
import { ActionToLabel } from "@goauthentik/admin/events/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/PageHeader";
import { KeyUnknown } from "@goauthentik/elements/forms/Form";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EventsApi } from "@goauthentik/api";

@customElement("ak-event-info-page")
export class EventInfoPage extends AKElement {
    @property()
    set eventID(value: string) {
        new EventsApi(DEFAULT_CONFIG)
            .eventsEventsRetrieve({
                eventUuid: value,
            })
            .then((ev) => {
                this.event = ev as EventWithContext;
            });
    }

    @property({ attribute: false })
    event!: EventWithContext;

    static get styles(): CSSResult[] {
        return [PFBase, PFGrid, PFDescriptionList, PFPage, PFContent, PFCard, AKGlobal];
    }

    render(): TemplateResult {
        if (!this.event) {
            return html`<ak-page-header icon="pf-icon pf-icon-catalog" header=${t`Loading`}>
            </ak-page-header> `;
        }
        let geo: KeyUnknown | undefined = undefined;
        if (Object.hasOwn(this.event.context, "geo")) {
            geo = this.event.context.geo as KeyUnknown;
        }
        return html`<ak-page-header
                icon="pf-icon pf-icon-catalog"
                header=${t`Event ${this.event.pk}`}
            >
            </ak-page-header>
            <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                <div class="pf-l-grid pf-m-gutter">
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-4-col-on-xl">
                        <div class="pf-c-card__title">${t`Event info`}</div>
                        <div class="pf-c-card__body">
                            <dl class="pf-c-description-list pf-m-horizontal">
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Action`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${ActionToLabel(this.event.action)}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text">${t`App`}</span>
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.event.app}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text">${t`User`}</span>
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.event.user?.username
                                                ? html`<div>
                                                          <a
                                                              href="#/identity/users/${this.event
                                                                  .user.pk}"
                                                              >${this.event.user?.username}</a
                                                          >
                                                      </div>
                                                      ${this.event.user.on_behalf_of
                                                          ? html`<small>
                                                                <a
                                                                    href="#/identity/users/${this
                                                                        .event.user.on_behalf_of
                                                                        .pk}"
                                                                    >${t`On behalf of ${this.event.user.on_behalf_of.username}`}</a
                                                                >
                                                            </small>`
                                                          : html``}`
                                                : html`-`}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Created`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.event.created?.toLocaleString()}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Client IP`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            <div>${this.event.clientIp || t`-`}</div>
                                            ${geo
                                                ? html`<small
                                                      >${[geo.city, geo.country].join(", ")}</small
                                                  >`
                                                : html``}
                                        </div>
                                    </dd>
                                </div>
                                <div class="pf-c-description-list__group">
                                    <dt class="pf-c-description-list__term">
                                        <span class="pf-c-description-list__text"
                                            >${t`Tenant`}</span
                                        >
                                    </dt>
                                    <dd class="pf-c-description-list__description">
                                        <div class="pf-c-description-list__text">
                                            ${this.event.tenant?.name || t`-`}
                                        </div>
                                    </dd>
                                </div>
                            </dl>
                        </div>
                    </div>
                    <div class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-8-col-on-xl">
                        <ak-event-info .event=${this.event}></ak-event-info>
                    </div>
                </div>
            </section>`;
    }
}
