import "#elements/EmptyState";
import "chartjs-adapter-date-fns";

import { EVENT_REFRESH, EVENT_THEME_CHANGE } from "#common/constants";
import { APIError, parseAPIResponseError, pluckErrorDetail } from "#common/errors/network";
import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";

import { UiThemeEnum } from "@goauthentik/api";

import {
    ArcElement,
    BarController,
    BarElement,
    Chart,
    ChartConfiguration,
    ChartData,
    ChartOptions,
    DoughnutController,
    Filler,
    Legend,
    LinearScale,
    LineController,
    LineElement,
    Plugin,
    PointElement,
    Tick,
    TimeScale,
    TimeSeriesScale,
    Tooltip,
} from "chart.js";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

Chart.register(Legend, Tooltip);
Chart.register(LineController, BarController, DoughnutController);
Chart.register(ArcElement, BarElement, PointElement, LineElement);
Chart.register(TimeScale, TimeSeriesScale, LinearScale, Filler);

export const FONT_COLOUR_DARK_MODE = "#fafafa";
export const FONT_COLOUR_LIGHT_MODE = "#151515";

export abstract class AKChart<T> extends AKElement {
    public role = "figure";

    abstract apiRequest(): Promise<T>;
    abstract getChartData(data: T): ChartData;

    @state()
    chart?: Chart;

    @state()
    error?: APIError;

    @property()
    centerText?: string;

    fontColour = FONT_COLOUR_LIGHT_MODE;

    static styles: CSSResult[] = [
        css`
            .container {
                height: 100%;
                width: 100%;

                display: flex;
                justify-content: center;
                align-items: center;
                position: relative;
            }
            .container > span {
                position: absolute;
                font-size: 2.5rem;
            }
            canvas {
                width: 100px;
                height: 100px;
                z-index: 1;
                cursor: crosshair;
            }
        `,
    ];

    connectedCallback(): void {
        super.connectedCallback();
        window.addEventListener("resize", this.resizeHandler);
        this.addEventListener(EVENT_REFRESH, this.refreshHandler);
        this.addEventListener(EVENT_THEME_CHANGE, ((ev: CustomEvent<UiThemeEnum>) => {
            if (ev.detail === UiThemeEnum.Light) {
                this.fontColour = FONT_COLOUR_LIGHT_MODE;
            } else {
                this.fontColour = FONT_COLOUR_DARK_MODE;
            }
            this.chart?.update();
        }) as EventListener);
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
        this.apiRequest()
            .then((r) => {
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
            })
            .catch(async (error: unknown) => {
                const parsedError = await parseAPIResponseError(error);
                this.error = parsedError;
            });
    }

    getChartType(): string {
        return "bar";
    }

    getPlugins(): Plugin[] {
        return [];
    }

    timeTickCallback(tickValue: string | number, index: number, ticks: Tick[]): string {
        const valueStamp = ticks[index];
        return formatElapsedTime(new Date(valueStamp.value));
    }

    getOptions(): ChartOptions {
        return {
            maintainAspectRatio: false,
            responsive: true,
            scales: {
                x: {
                    type: "timeseries",
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
                ${this.error
                    ? html`
                          <ak-empty-state icon="fa-times"
                              ><span>${msg("Failed to fetch data.")}</span>
                              <p slot="body">${pluckErrorDetail(this.error)}</p>
                          </ak-empty-state>
                      `
                    : html`${this.chart ? nothing : html`<ak-empty-state loading></ak-empty-state>`}`}
                ${this.centerText ? html` <span>${this.centerText}</span> ` : nothing}
                <canvas
                    role="img"
                    aria-label=${msg("Chart")}
                    style="${!this.chart ? "display: none;" : ""}"
                ></canvas>
            </div>
        `;
    }
}
