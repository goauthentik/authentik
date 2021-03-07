import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Event, EventsApi } from "../../api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { COMMON_STYLES } from "../../common/styles";
import "./EventInfo";

@customElement("ak-event-info-page")
export class EventInfoPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.eventID = value.id;
    }

    @property()
    set eventID(value: string) {
        new EventsApi(DEFAULT_CONFIG).eventsEventsRead({
            eventUuid: value
        }).then((ev) => {
            this.event = ev;
        });
    }

    @property({ attribute: false })
    event!: Event;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(css`
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
