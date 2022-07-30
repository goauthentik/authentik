import { EVENT_REFRESH } from "@goauthentik/web/constants";
import {
    FONT_COLOUR_DARK_MODE,
    FONT_COLOUR_LIGHT_MODE,
} from "@goauthentik/web/pages/flows/FlowDiagram";
import { Chart, ChartConfiguration, ChartData, ChartOptions, Plugin, Tick } from "chart.js";
import { Legend, Tooltip } from "chart.js";
import { BarController, DoughnutController, LineController } from "chart.js";
import { ArcElement, BarElement } from "chart.js";
import { LinearScale, TimeScale } from "chart.js";
import "chartjs-adapter-moment";

import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { property } from "lit/decorators.js";

Chart.register(Legend, Tooltip);
Chart.register(LineController, BarController, DoughnutController);
Chart.register(ArcElement, BarElement);
Chart.register(TimeScale, LinearScale);

export abstract class AKChart<T> extends LitElement {
    abstract apiRequest(): Promise<T>;
    abstract getChartData(data: T): ChartData;

    chart?: Chart;

    @property()
    centerText?: string;

    fontColour = FONT_COLOUR_LIGHT_MODE;

    static get styles(): CSSResult[] {
        return [
            css`
                .container {
                    height: 100%;
                }
                canvas {
                    width: 100px;
                    height: 100px;
                }
            `,
        ];
    }

    constructor() {
        super();
        window.addEventListener("resize", () => {
            if (this.chart) {
                this.chart.resize();
            }
        });
        window.addEventListener(EVENT_REFRESH, () => {
            this.apiRequest().then((r: T) => {
                if (!this.chart) return;
                this.chart.data = this.getChartData(r);
                this.chart.update();
            });
        });
        const matcher = window.matchMedia("(prefers-color-scheme: light)");
        const handler = (ev?: MediaQueryListEvent) => {
            if (ev?.matches || matcher.matches) {
                this.fontColour = FONT_COLOUR_LIGHT_MODE;
            } else {
                this.fontColour = FONT_COLOUR_DARK_MODE;
            }
            this.chart?.update();
        };
        matcher.addEventListener("change", handler);
        handler();
    }

    firstUpdated(): void {
        this.apiRequest().then((r) => {
            const canvas = this.shadowRoot?.querySelector<HTMLCanvasElement>("canvas");
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

    getChartType(): string {
        return "bar";
    }

    getPlugins(): Plugin[] {
        return [
            {
                id: "center-text",
                beforeDraw: (chart) => {
                    if (!chart.ctx) return;
                    if (!this.centerText) return;
                    const width = chart.width || 0;
                    const height = chart.height || 0;

                    const fontSize = (height / 114).toFixed(2);
                    chart.ctx.font = `${fontSize}em Overpass, Arial, sans-serif`;
                    chart.ctx.textBaseline = "middle";
                    chart.ctx.fillStyle = this.fontColour;

                    const textX = Math.round(
                        (width - chart.ctx.measureText(this.centerText).width) / 2,
                    );
                    const textY = height / 2;

                    chart.ctx.fillText(this.centerText, textX, textY);
                },
            },
        ];
    }

    timeTickCallback(tickValue: string | number, index: number, ticks: Tick[]): string {
        const valueStamp = ticks[index];
        const delta = Date.now() - valueStamp.value;
        const ago = Math.round(delta / 1000 / 3600);
        return t`${ago} hours ago`;
    }

    getOptions(): ChartOptions {
        return {
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: "time",
                    display: true,
                    ticks: {
                        callback: (tickValue: string | number, index: number, ticks: Tick[]) => {
                            return this.timeTickCallback(tickValue, index, ticks);
                        },
                        autoSkip: true,
                        maxTicksLimit: 8,
                    },
                    stacked: true,
                    grid: {
                        color: "rgba(0, 0, 0, 0)",
                    },
                    offset: true,
                },
                y: {
                    type: "linear",
                    display: true,
                    stacked: true,
                    grid: {
                        color: "rgba(0, 0, 0, 0)",
                    },
                },
            },
        } as ChartOptions;
    }

    configureChart(data: T, ctx: CanvasRenderingContext2D): Chart {
        const config = {
            type: this.getChartType(),
            data: this.getChartData(data),
            options: this.getOptions(),
            plugins: this.getPlugins(),
        };
        return new Chart(ctx, config as ChartConfiguration);
    }

    render(): TemplateResult {
        return html`
            <div class="container">
                <canvas></canvas>
            </div>
        `;
    }
}
