import { css, CSSResult, html, LitElement, TemplateResult } from "lit-element";
import Chart from "chart.js";

interface TickValue {
    value: number;
    major: boolean;
}

export abstract class AKChart<T> extends LitElement {

    abstract apiRequest(): Promise<T>;
    abstract getDatasets(data: T): Chart.ChartDataSets[];

    chart?: Chart;

    static get styles(): CSSResult[] {
        return [css`
            :host {
                position: relative;
                height: 100%;
                width: 100%;
                display: block;
                min-height: 25rem;
            }
            canvas {
                width: 100px;
                height: 100px;
            }
        `];
    }

    constructor() {
        super();
        window.addEventListener("resize", () => {
            if (this.chart) {
                this.chart.resize();
            }
        });
    }

    configureChart(data: T, ctx: CanvasRenderingContext2D): Chart {
        return new Chart(ctx, {
            type: "bar",
            data: {
                datasets: this.getDatasets(data),
            },
            options: {
                maintainAspectRatio: false,
                spanGaps: true,
                scales: {
                    xAxes: [
                        {
                            stacked: true,
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                            },
                            type: "time",
                            offset: true,
                            ticks: {
                                callback: function (value, index: number, values) {
                                    const valueStamp = <TickValue>(<unknown>values[index]);
                                    const delta = Date.now() - valueStamp.value;
                                    const ago = Math.round(delta / 1000 / 3600);
                                    return `${ago} Hours ago`;
                                },
                                autoSkip: true,
                                maxTicksLimit: 8,
                            },
                        },
                    ],
                    yAxes: [
                        {
                            stacked: true,
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                            },
                        },
                    ],
                },
            },
        });
    }

    firstUpdated(): void {
        this.apiRequest().then((r) => {
            const canvas = <HTMLCanvasElement>this.shadowRoot?.querySelector("canvas");
            if (!canvas) {
                console.warn("Failed to get canvas element");
                return false;
            }
            const ctx = canvas.getContext("2d");
            if (!ctx) {
                console.warn("failed to get 2d context");
                return false;
            }
            this.chart = this.configureChart(r, ctx);
        });
    }

    render(): TemplateResult {
        return html`<canvas></canvas>`;
    }
}
