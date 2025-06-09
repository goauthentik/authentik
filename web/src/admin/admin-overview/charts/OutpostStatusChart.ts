import { AKElement } from "#elements/Base";
import { actionToColor } from "#elements/charts/EventChart";
import { SummarizedSyncStatus } from "@goauthentik/admin/admin-overview/charts/SyncStatusChart";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKChart } from "@goauthentik/elements/charts/Chart";
import "@goauthentik/elements/forms/ConfirmationForm";
import { ChartData, ChartOptions } from "chart.js";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { EventActions, OutpostsApi } from "@goauthentik/api";

export type OutpostState = "healthy" | "outdated" | "unhealthy";

export interface OutpostStatus {
    state: OutpostState;
    label: string;
}

@customElement("ak-admin-status-chart-outpost")
export class OutpostStatusChart extends AKElement {
    @state()
    data?: OutpostStatus[];

    static get styles() {
        return [
            PFBase,
            css`
                :host {
                    --square-size: 3rem;
                    --square-border: 1px;
                }
                .container {
                }
                .grid {
                    display: grid;
                    grid-template-columns: repeat(
                        auto-fill,
                        calc(var(--square-size) + var(--square-border))
                    );
                }
                .square {
                    width: var(--square-size);
                    height: var(--square-size);
                    margin: var(--square-border);
                    margin-top: 0;
                }
                .healthy {
                    background-color: #4cb140;
                }
                .outdated {
                    background-color: #0060c0;
                }
                .unhealthy {
                    background-color: #c46100;
                }
            `,
        ];
    }

    async apiRequest(): Promise<OutpostStatus[]> {
        const api = new OutpostsApi(DEFAULT_CONFIG);
        const outposts = await api.outpostsInstancesList({});
        const outpostStats: OutpostStatus[] = [];
        await Promise.all(
            outposts.results.map(async (element) => {
                const health = await api.outpostsInstancesHealthList({
                    uuid: element.pk,
                });
                health.forEach((h) => {
                    const singleStats: OutpostStatus = {
                        label: `${element.name} - ${h.hostname}`,
                        state: "unhealthy",
                    };
                    if (h.versionOutdated) {
                        singleStats.state = "outdated";
                    } else if (h.lastSeen.getTime() <= new Date().getTime() - 60 * 10 * 1000) {
                        singleStats.state = "unhealthy";
                    } else {
                        singleStats.state = "healthy";
                    }
                    outpostStats.push(singleStats);
                });
            }),
        );

        outpostStats.sort((a, b) => a.label.localeCompare(b.label));
        return outpostStats;
    }

    firstUpdated() {
        this.apiRequest().then((data) => (this.data = data));
    }

    render() {
        if (!this.data) {
            return nothing;
        }
        return html`<div class="container"><div class="grid">
            ${this.data.map((d) => {
                return html`<div class="square ${d.state}"></div>`;
            })}
        </div></div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-status-chart-outpost": OutpostStatusChart;
    }
}
