import Styles from "./Timestamp.styles";

import { formatElapsedTime } from "#common/temporal";

import { AKElement } from "#elements/Base";
import { intersectionObserver } from "#elements/decorators/intersection-observer";
import { ifPresent } from "#elements/utils/attributes";
import { dateProperty } from "#elements/utils/properties";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-timestamp")
export class AKTimestamp extends AKElement {
    static readonly styles = [Styles];

    @property(dateProperty)
    public get timestamp(): Date | null {
        return this.#timestamp;
    }

    public set timestamp(value: string | Date | number | null) {
        const date = value ? (value instanceof Date ? value : new Date(value)) : null;

        // An unparseable value returns an Invalid Date, which is truthy but still can't be formatted.
        this.#timestamp = date && !Number.isNaN(date.getTime()) ? date : null;
    }

    @intersectionObserver()
    public visible = false;

    @property({ type: Boolean, attribute: "hide-elapsed" })
    public hideElapsed: boolean = false;

    @property({ type: Boolean })
    public datetime: boolean = false;

    @property({ type: Boolean })
    public dateOnly: boolean = false;

    @property({ type: Boolean })
    public refresh: boolean = false;

    public static updateDelay = 60;

    protected static reducedMotionMediaQuery: MediaQueryList | null = null;

    #timestamp: Date | null = null;

    #interval = -1;
    #animationFrameID = -1;

    public connectedCallback(): void {
        super.connectedCallback();
        document.addEventListener("visibilitychange", this.startInterval);
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        document.removeEventListener("visibilitychange", this.startInterval);
        AKTimestamp.reducedMotionMediaQuery?.removeEventListener("change", this.startInterval);
        this.stopInterval();
        cancelAnimationFrame(this.#animationFrameID);
    }

    protected override updated(changed: PropertyValues<this>): void {
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

        if (!AKTimestamp.reducedMotionMediaQuery) {
            AKTimestamp.reducedMotionMediaQuery = window.matchMedia(
                "(prefers-reduced-motion: reduce)",
            );
        }

        AKTimestamp.reducedMotionMediaQuery.addEventListener("change", this.startInterval);

        const moment = this.timestamp.getTime();
        const start = Date.now();
        const { updateDelay, reducedMotionMediaQuery } = AKTimestamp;
        const updateInterval = updateDelay * 1000;

        const startWithinInterval =
            start >= moment - updateInterval && start <= moment + updateInterval;

        // Adjust interval based on how close we are to the minute mark,
        // allowing the elapsed time to at first update every second for the first minute,
        // then every minute afterwards.

        if (startWithinInterval && !reducedMotionMediaQuery.matches) {
            this.#interval = self.setInterval(() => {
                if (!this.visible || document.visibilityState !== "visible") return;

                this.requestUpdate();

                const now = Date.now();

                if (now < moment - updateInterval || now > moment + updateInterval) {
                    this.startInterval();
                }
            }, 1000);
        } else {
            this.#interval = self.setInterval(() => {
                if (!this.visible || document.visibilityState !== "visible") return;

                this.requestUpdate();
            }, updateInterval);
        }
    };

    public render() {
        if (!this.timestamp || this.timestamp.getTime() === 0) {
            return html`<span role="time" aria-label=${msg("None")}>-</span>`;
        }

        const elapsed = formatElapsedTime(this.timestamp);

        return html` <time
            datetime=${this.timestamp.toISOString()}
            aria-labelledby="timestamp-label"
            aria-describedby=${ifPresent(!this.hideElapsed, "elapsed")}
        >
            <div part="label" id="timestamp-label">
                <slot></slot>
            </div>
            ${!this.hideElapsed ? html`<div part="elapsed" id="elapsed">${elapsed}</div>` : nothing}
            ${
                this.datetime
                    ? html`<small part="datetime" id="datetime"
                          >${
                              this.dateOnly
                                  ? this.timestamp.toLocaleDateString()
                                  : this.timestamp.toLocaleString()
                          }</small
                      >`
                    : nothing
            }
        </time>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-timestamp": AKTimestamp;
    }
}
