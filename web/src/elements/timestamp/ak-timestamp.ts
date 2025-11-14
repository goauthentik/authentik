import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";
import { intersectionObserver } from "#elements/decorators/intersection-observer";
import { ifPresent } from "#elements/utils/attributes";

import { html, nothing, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-timestamp")
export class AKTimestamp extends AKElement {
    #timestamp: Date | null = null;

    @property({
        attribute: false,
        hasChanged(value, previousValue) {
            if (value instanceof Date && previousValue instanceof Date) {
                return value.getTime() !== previousValue.getTime();
            }
            return value !== previousValue;
        },
    })
    public get timestamp(): Date | null {
        return this.#timestamp;
    }

    public set timestamp(value: string | Date | number | null) {
        this.#timestamp = value ? (value instanceof Date ? value : new Date(value)) : null;
    }

    @intersectionObserver()
    public visible = false;

    @property({ type: Boolean, useDefault: true })
    public elapsed: boolean = true;

    @property({ type: Boolean, useDefault: true })
    public datetime: boolean = false;

    @property({ type: Boolean, useDefault: true })
    public refresh: boolean = false;

    #interval = -1;
    #animationFrameID = -1;

    public connectedCallback(): void {
        super.connectedCallback();
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.stopInterval();
        cancelAnimationFrame(this.#animationFrameID);
    }

    public updated(changed: PropertyValues<this>): void {
        super.updated(changed);

        if (changed.has("visible") || changed.has("timestamp") || changed.has("refresh")) {
            cancelAnimationFrame(this.#animationFrameID);
            this.#animationFrameID = requestAnimationFrame(this.startInterval);
        }
    }

    public stopInterval = () => {
        clearInterval(this.#interval);
    };

    public startInterval = () => {
        this.stopInterval();

        if (
            !this.timestamp ||
            !this.refresh ||
            document.visibilityState !== "visible" ||
            !this.visible
        ) {
            return;
        }

        const moment = this.timestamp.getTime();
        const start = Date.now();

        // Adjust interval based on how close we are to the minute mark,
        // allowing the elapsed time to at first update every second for the first minute,
        // then every minute afterwards.

        if (start >= moment - 60000 && start <= moment + 60000) {
            this.#interval = self.setInterval(() => {
                if (!this.visible || document.visibilityState !== "visible") return;

                this.requestUpdate();

                const now = Date.now();

                if (now < moment - 60000 || now > moment + 60000) {
                    this.startInterval();
                }
            }, 1000);
        } else {
            this.#interval = self.setInterval(() => {
                if (!this.visible || document.visibilityState !== "visible") return;

                this.requestUpdate();
            }, 1000 * 60);
        }
    };

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
