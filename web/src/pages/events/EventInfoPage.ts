import { t } from "@lingui/macro";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { EventsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { EventWithContext } from "../../api/Events";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import AKGlobal from "../../authentik.css";
import "./EventInfo";
import "../../elements/PageHeader";

@customElement("ak-event-info-page")
export class EventInfoPage extends LitElement {

    @property()
    set eventID(value: string) {
        new EventsApi(DEFAULT_CONFIG).eventsEventsRead({
            eventUuid: value
        }).then((ev) => {
            this.event = ev as EventWithContext;
        });
    }

    @property({ attribute: false })
    event!: EventWithContext;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFContent, PFCard, AKGlobal].concat(css`
            .pf-c-card {
                color: var(--ak-dark-foreground);
            }
        `);
    }

    render(): TemplateResult {
        return html`<ak-page-header
            icon="pf-icon pf-icon-catalog"
            header=${t`Event ${this.event?.pk || ""}`}>
        </ak-page-header>
        <section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <div class="pf-c-card">
                <div class="pf-c-card__title">
                    ${t`Event info`}
                </div>
                <div class="pf-c-card__body">
                    <ak-event-info .event=${this.event}></ak-event-info>
                </div>
            </div>
        </section>`;
    }

}
