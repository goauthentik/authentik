import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { AKElement } from "@goauthentik/elements/Base";
import {
    Chart,
    ChartConfiguration,
    ChartData,
    ChartOptions,
    Filler,
    LineElement,
    Plugin,
    PointElement,
    Tick,
} from "chart.js";
import { Legend, Tooltip } from "chart.js";
import { BarController, DoughnutController, LineController } from "chart.js";
import { ArcElement, BarElement } from "chart.js";
import { LinearScale, TimeScale } from "chart.js";
import "chartjs-adapter-moment";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { property } from "lit/decorators.js";

Chart.register(Legend, Tooltip);
Chart.register(LineController, BarController, DoughnutController);
Chart.register(ArcElement, BarElement, PointElement, LineElement);
Chart.register(TimeScale, LinearScale, Filler);

export const FONT_COLOUR_DARK_MODE = "#fafafa";
export const FONT_COLOUR_LIGHT_MODE = "#151515";

export class RGBAColor {
    constructor(public r: number, public g: number, public b: number, public a: number = 1) {}
    toString(): string {
        return `rgba(${this.r}, ${this.g}, ${this.b}, ${this.a})`;
    }
}

export function getColorFromString(stringInput: string): RGBAColor {
    let hash = 0;
    for (let i = 0; i < stringInput.length; i++) {
        hash = stringInput.charCodeAt(i) + ((hash << 5) - hash);
        hash = hash & hash;
    }
    const rgb = [0, 0, 0];
    for (let i = 0; i < 3; i++) {
        const value = (hash >> (i * 8)) & 255;
        rgb[i] = value;
    }
    return new RGBAColor(rgb[0], rgb[1], rgb[2]);
}

export abstract class AKChart<T> extends AKElement {
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

    connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener("resize", this.resizeHandler);
        this.addEventListener(EVENT_REFRESH, this.refreshHandler);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener("resize", this.resizeHandler);
        this.removeEventListener(EVENT_REFRESH, this.refreshHandler);
    }

    refreshHandler(): void {
        this.apiRequest().then((r: T) => {
            if (!this.chart) return;
            this.chart.data = this.getChartData(r);
            this.chart.update();
        });
    }

    resizeHandler(): void {
        if (!this.chart) {
            return;
        }
        this.chart.resize();
    }

    firstUpdated(): void {
        this.apiRequest().then((r) => {
            const canvas = this.shadowRoot?.querySelector<HTMLCanvasElement>("canvas");
            if (!canvas) {
                console.warn("Failed to get canvas element");
                return;
            }
            const ctx = canvas.getContext("2d");
            if (!ctx) {
                console.warn("failed to get 2d context");
                return;
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
