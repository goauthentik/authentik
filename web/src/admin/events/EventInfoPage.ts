import "@goauthentik/admin/events/EventInfo";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EventWithContext } from "@goauthentik/common/events";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/PageHeader";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
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
        return [PFBase, PFPage, PFContent, PFCard, AKGlobal];
    }

    render(): TemplateResult {
        return html`<ak-page-header
                icon="pf-icon pf-icon-catalog"
                header=${t`Event ${this.event?.pk || ""}`}
            >
            </ak-page-header>
            <section class="pf-c-page__main-section pf-m-no-padding-mobile">
                <div class="pf-c-card">
                    <div class="pf-c-card__title">${t`Event info`}</div>
                    <div class="pf-c-card__body">
                        <ak-event-info .event=${this.event}></ak-event-info>
                    </div>
                </div>
            </section>`;
    }
}
