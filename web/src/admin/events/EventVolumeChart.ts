import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import { ChartData } from "chart.js";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { Coordinate, EventsApi, EventsEventsListRequest } from "@goauthentik/api";

@customElement("ak-events-volume-chart")
export class EventVolumeChart extends AKChart<Coordinate[]> {
    @property({ attribute: "with-map", type: Boolean })
    withMap = false;

    _query?: EventsEventsListRequest;

    @property({ attribute: false })
    set query(value: EventsEventsListRequest | undefined) {
        if (JSON.stringify(value) !== JSON.stringify(this._query)) return;
        this._query = value;
        this.refreshHandler();
    }

    static get styles(): CSSResult[] {
        return super.styles.concat(
            PFCard,
            css`
                :host([with-map]) .pf-c-card {
                    height: 24rem;
                }
            `,
        );
    }

    apiRequest(): Promise<Coordinate[]> {
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList(this._query);
    }

    getChartData(data: Coordinate[]): ChartData {
        return {
            datasets: [
                {
                    label: msg("Events"),
                    backgroundColor: "rgba(189, 229, 184, .5)",
                    spanGaps: true,
                    data:
                        data.map((cord) => {
                            return {
                                x: cord.xCord || 0,
                                y: cord.yCord || 0,
                            };
                        }) || [],
                },
            ],
        };
    }

    render(): TemplateResult {
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">${msg("Event volume")}</div>
            <div class="pf-c-card__body">${super.render()}</div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-events-volume-chart": EventVolumeChart;
    }
}
