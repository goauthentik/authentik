import { css, CSSResult, html, LitElement, TemplateResult } from "lit-element";
import { Chart, ChartDataset, Tick, LineController, TimeScale, LinearScale, BarController, BarElement, ChartConfiguration, Legend } from "chart.js";
import "chartjs-adapter-moment";

Chart.register(LineController, TimeScale, LinearScale, BarController, BarElement, Legend);

export abstract class AKChart<T> extends LitElement {

    abstract apiRequest(): Promise<T>;
    abstract getDatasets(data: T): ChartDataset[];

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
        const config = {
            type: "bar",
            data: {
                datasets: this.getDatasets(data),
            },
            options: {
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: "time",
                        display: true,
                        ticks: {
                            callback: function (tickValue: string | number, index: number, ticks: Tick[]): string {
                                const valueStamp = (ticks[index]);
                                const delta = Date.now() - valueStamp.value;
                                const ago = Math.round(delta / 1000 / 3600);
                                return `${ago} Hours ago`;
                            },
                            autoSkip: true,
                            maxTicksLimit: 8,
                        },
                        stacked: true,
                        grid: {
                            color: "rgba(0, 0, 0, 0)",
                        },
                        offset: true
                    },
                    y: {
                        type: "linear",
                        display: true,
                        stacked: true,
                        grid: {
                            color: "rgba(0, 0, 0, 0)",
                        },
                    }
                },
            },
        };
        return new Chart(ctx, config as ChartConfiguration);
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
