import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { Event } from "../../api/Events";
import { COMMON_STYLES } from "../../common/styles";

@customElement("ak-event-info-page")
export class EventInfoPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.eventID = value.id;
    }

    @property()
    set eventID(value: string) {
        Event.get(value).then((e) => (this.event = e));
    }

    @property({ attribute: false })
    event?: Event;

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
