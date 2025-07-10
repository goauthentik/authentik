import { EventChart } from "#elements/charts/EventChart";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { ChartData } from "chart.js";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { EventVolume, EventsApi, EventsEventsListRequest } from "@goauthentik/api";

@customElement("ak-events-volume-chart")
export class EventVolumeChart extends EventChart {
    @property({ attribute: "with-map", type: Boolean })
    withMap = false;

    _query?: EventsEventsListRequest;

    @property({ attribute: false })
    set query(value: EventsEventsListRequest | undefined) {
        if (JSON.stringify(value) !== JSON.stringify(this._query)) return;
        this._query = value;
        this.refreshHandler();
    }

    static styles: CSSResult[] = [
        ...super.styles,
        PFCard,
        css`
            :host([with-map]) .pf-c-card {
                height: 24rem;
            }
            .pf-c-card {
                height: 20rem;
            }
        `,
    ];

    apiRequest(): Promise<EventVolume[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList({
            historyDays: 7,
            ...this._query,
        });
    }

    getChartData(data: EventVolume[]): ChartData {
        return this.eventVolume(data, {
            padToDays: 7,
        });
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__body">${super.render()}</div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-volume-chart": EventVolumeChart;
    }
}
