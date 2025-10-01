import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";
import { ifPresent } from "#elements/utils/attributes";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-timestamp")
export class AKTimestamp extends AKElement {
    #timestamp: Date | null = null;

    @property({ attribute: false })
    public get timestamp(): Date | null {
        return this.#timestamp;
    }

    public set timestamp(value: string | Date | number | null) {
        this.#timestamp = value ? (value instanceof Date ? value : new Date(value)) : null;
    }

    @property({ type: Boolean })
    public elapsed: boolean = true;

    @property({ type: Boolean })
    public datetime: boolean = false;

    @property({ type: Boolean })
    public refresh: boolean = false;

    #interval = -1;

    public connectedCallback(): void {
        super.connectedCallback();

        if (this.refresh) {
            this.#interval = self.setInterval(() => {
                this.requestUpdate();
            }, 1000 * 60);
        }
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        if (this.#interval !== -1) {
            self.clearInterval(this.#interval);
        }
    }

    public render() {
        if (!this.timestamp || this.timestamp.getTime() === 0) {
            return html`<span role="time" aria-label="None">-</span>`;
        }

        const elapsed = formatElapsedTime(this.timestamp);

        return html` <time
            datetime=${this.timestamp.toISOString()}
            aria-labelledby="timestamp-label"
            aria-describedby=${ifPresent(this.elapsed, "elapsed")}
        >
            <div part="label" id="timestamp-label">
                <slot></slot>
            </div>
            ${this.elapsed ? html`<div part="elapsed" id="elapsed">${elapsed}</div>` : nothing}
            ${this.datetime
                ? html`<small part="datetime" id="datetime"
                      >${this.timestamp.toLocaleString()}</small
                  >`
                : nothing}
        </time>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-timestamp": AKTimestamp;
    }
}
