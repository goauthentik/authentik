import { css, customElement, html, LitElement, property } from "lit-element";
import Chart from "chart.js";

interface TickValue {
    value: number;
    major: boolean;
}

@customElement("pb-admin-logins-chart")
export class AdminLoginsChart extends LitElement {

    @property()
    url: string = "";

    chart: any;

    static get styles() {
        return css`
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
        `;
    }

    constructor() {
        super();
        window.addEventListener('resize', () => {
            if (this.chart) {
                this.chart.resize();
            }
        });
    }

    firstUpdated() {
        fetch(this.url).then(r => r.json()).catch(e => console.error(e)).then(r => {
            let ctx = (<HTMLCanvasElement>this.shadowRoot?.querySelector("canvas")).getContext('2d')!;
            this.chart = new Chart(ctx, {
                type: 'bar',
                data: {
                    datasets: [
                        {
                            label: 'Failed Logins',
                            backgroundColor: "rgba(201, 25, 11, .5)",
                            spanGaps: true,
                            data: r.logins_failed_per_1h,
                        },
                        {
                            label: 'Successful Logins',
                            backgroundColor: "rgba(189, 229, 184, .5)",
                            spanGaps: true,
                            data: r.logins_per_1h,
                        },
                    ]
                },
                options: {
                    maintainAspectRatio: false,
                    spanGaps: true,
                    scales: {
                        xAxes: [{
                            stacked: true,
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                            },
                            type: 'time',
                            offset: true,
                            ticks: {
                                callback: function (value, index: number, values) {
                                    const valueStamp = <TickValue>(<unknown>values[index]);
                                    const delta = (Date.now() - valueStamp.value);
                                    const ago = Math.round(delta / 1000 / 3600);
                                    return `${ago} Hours ago`;
                                },
                                autoSkip: true,
                                maxTicksLimit: 8
                            }
                        }],
                        yAxes: [{
                            stacked: true,
                            gridLines: {
                                color: "rgba(0, 0, 0, 0)",
                            }
                        }]
                    }
                }
            });
        });
    }

    render() {
        return html`<canvas></canvas>`;
    }

}
