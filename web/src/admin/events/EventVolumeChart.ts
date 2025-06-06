import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import { ChartData } from "chart.js";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { EventVolume, EventsApi, EventsEventsListRequest } from "@goauthentik/api";

@customElement("ak-events-volume-chart")
export class EventVolumeChart extends AKChart<EventVolume[]> {
    _query?: EventsEventsListRequest;

    @property({ attribute: false })
    set query(value: EventsEventsListRequest | undefined) {
        this._query = value;
        this.refreshHandler();
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFCard,
            css`
                .pf-c-card {
                    height: 20rem;
                }
            `,
        );
    }

    apiRequest(): Promise<EventVolume[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList({
            historyDays: 14,
            ...this._query
        });
    }

    getChartData(data: EventVolume[]): ChartData {
        return this.eventVolume(data);
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
