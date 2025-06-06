import { actionToLabel } from "#common/labels";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart, getColorFromString } from "@goauthentik/elements/charts/Chart";
import { ChartData } from "chart.js";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFCard from "@patternfly/patternfly/components/Card/card.css";

import { EventActions, EventVolume, EventsApi, EventsEventsListRequest } from "@goauthentik/api";

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
        return new EventsApi(DEFAULT_CONFIG).eventsEventsVolumeList(this._query);
    }

    getChartData(data: EventVolume[]): ChartData {
        const datasets: ChartData = {
            datasets: [],
        };
        // Get a list of all actions
        const actions = new Set(data.map((v) => v.action));
        actions.forEach((action) => {
            const actionData: { x: number; y: number }[] = [];
            data.filter((v) => v.action === action).forEach((v) => {
                actionData.push({
                    x: v.day.getTime(),
                    y: v.count,
                });
            });
            datasets.datasets.push({
                label: actionToLabel(action as EventActions),
                backgroundColor: getColorFromString(action),
                spanGaps: true,
                data: actionData,
            });
        });
        return datasets;
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
