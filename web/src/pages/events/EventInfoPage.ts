import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { EventsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { EventWithContext } from "../../api/Events";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import AKGlobal from "../../authentik.css";
import "./EventInfo";

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
        return [PFBase, PFPage, PFCard, AKGlobal].concat(css`
            .pf-c-card {
                color: var(--ak-dark-foreground);
            }
        `);
    }

    render(): TemplateResult {
        return html`<section class="pf-c-page__main-section pf-m-light">
            <div class="pf-c-content">
                <h1>
                    <i class="pf-icon pf-icon-catalog"></i>
                    ${gettext(`Event ${this.event?.pk || ""}`)}
                </h1>
            </div>
        </section>
        <section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <div class="pf-c-card">
                <div class="pf-c-card__body">
                    <ak-event-info .event=${this.event}></ak-event-info>
                </div>
            </div>
        </section>`;
    }

}
