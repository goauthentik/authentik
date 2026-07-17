import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

/**
 * PatternFly banner color modifiers, named by severity. Maps onto the blue/gold/red
 * scheme used for update/expiry/security notices.
 */
export enum BannerLevel {
    Info = "pf-m-blue",
    Warning = "pf-m-gold",
    Danger = "pf-m-red",
}

/**
 * @class Banner
 * @element ak-banner
 *
 * A sticky, full-width notice for surfacing instance-wide conditions to
 * administrators — missing configuration, a pending upgrade, an expiring
 * license or certificate, and so on. Presentational only: each caller decides
 * *when* to show the banner and supplies the message (and any action link) as
 * slotted content.
 *
 * Set `dismiss-key` to make the banner dismissible; the dismissal is remembered
 * in `localStorage` under that key. Omit it for notices that must stay visible
 * until the underlying condition is resolved.
 */
@customElement("ak-banner")
export class Banner extends AKElement {
    /**
     * Severity of the banner, controlling its color.
     *
     * @attr
     */
    @property()
    level: BannerLevel = BannerLevel.Warning;

    /**
     * Whether the banner sticks to the top of the viewport.
     *
     * @attr
     */
    @property({ type: Boolean })
    sticky = true;

    /**
     * Optional call-to-action link, rendered after the message. Provided as
     * properties (rather than a slotted `<a>`) so the anchor lives inside this
     * element's shadow root, where PatternFly's `.pf-c-banner a` rule can give
     * it a readable, on-brand color — a slotted anchor would instead inherit the
     * default blue link color from the caller's own `patternfly-base` styles.
     *
     * @attr
     */
    @property({ attribute: "action-href" })
    actionHref?: string;

    @property({ attribute: "action-label" })
    actionLabel?: string;

    /**
     * When set, renders a dismiss button and remembers the dismissal under this
     * key. Omit for non-dismissible notices.
     *
     * @attr
     */
    @property({ attribute: "dismiss-key" })
    dismissKey?: string;

    @state()
    protected dismissed = false;

    static styles = [
        PFBanner,
        css`
            .pf-c-banner {
                position: relative;
            }
            .pf-c-banner a {
                margin-inline-start: 0.25rem;
            }
            button {
                position: absolute;
                top: 50%;
                right: var(--pf-global--spacer--md, 1rem);
                transform: translateY(-50%);
                padding: 0;
                background: transparent;
                border: 0;
                color: inherit;
                cursor: pointer;
            }
        `,
    ];

    connectedCallback(): void {
        super.connectedCallback();
        if (this.dismissKey) {
            this.dismissed = localStorage.getItem(this.storageKey) === "1";
        }
    }

    private get storageKey(): string {
        return `ak-banner-dismissed:${this.dismissKey}`;
    }

    private dismiss(): void {
        this.dismissed = true;
        if (this.dismissKey) {
            localStorage.setItem(this.storageKey, "1");
        }
    }

    render() {
        if (this.dismissed) return nothing;

        return html`<div
            class=${classMap({
                "pf-c-banner": true,
                "pf-m-sticky": this.sticky,
                [this.level]: true,
            })}
        >
            <slot></slot>${this.actionHref && this.actionLabel
                ? html`<a href=${this.actionHref}>${this.actionLabel}</a>`
                : nothing}
            ${this.dismissKey
                ? html`<button
                      part="dismiss"
                      @click=${() => this.dismiss()}
                      aria-label=${msg("Dismiss", { id: "banner.dismiss.aria-label" })}
                  >
                      <i class="fas fa-times" aria-hidden="true"></i>
                  </button>`
                : nothing}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-banner": Banner;
    }
}
