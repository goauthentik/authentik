import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";

import {
    P4BannerDispositionClassName,
    P4BannerDispositionIconClassName,
    P4Disposition,
} from "#styles/patternfly/constants";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { guard } from "lit-html/directives/guard.js";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";

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
    static styles = [
        PFBanner,
        PFButton,
        css`
            .pf-c-banner {
                align-items: center;
                position: relative;
                display: flex;
                gap: var(--pf-global--spacer--sm);
            }

            [part="content"] {
                flex: 1 1 auto;
                display: block;
            }
        `,
    ];
    /**
     * Severity of the banner, controlling its color.
     *
     * @attr
     */
    @property({ type: String })
    public level: P4Disposition = P4Disposition.Warning;

    /**
     * Whether the banner sticks to the top of the viewport.
     *
     * @attr
     */
    @property({ type: Boolean })
    public sticky = true;

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
    public actionHref: string | null = null;

    /**
     * Label for the call-to-action link. Omit to render no link.
     *
     * @attr
     */
    @property({ attribute: "action-label" })
    public actionLabel: string | null = null;

    /**
     * When set, renders a dismiss button and remembers the dismissal under this
     * key. Omit for non-dismissible notices.
     *
     * @attr
     */
    @property({ attribute: "dismiss-key" })
    public dismissKey: string | null = null;

    @state()
    protected dismissed = false;

    public override connectedCallback(): void {
        super.connectedCallback();

        if (this.dismissKey) {
            this.dismissed = localStorage.getItem(this.storageKey) !== null;
        }
    }

    private get storageKey(): string {
        return `ak-banner-dismissed:${this.dismissKey}`;
    }

    private dismiss = (): void => {
        this.dismissed = true;

        if (this.dismissKey) {
            localStorage.setItem(this.storageKey, Date.now().toString());
        }
    };

    protected override render(): SlottedTemplateResult {
        const { dismissed, dismissKey, level, sticky, actionHref, actionLabel } = this;

        return guard([dismissed, level, sticky, actionHref, actionLabel], () => {
            if (dismissed) return null;

            const dispositionClass = P4BannerDispositionClassName[level];
            const iconClass = P4BannerDispositionIconClassName[level];

            return html`<div
                class=${classMap({
                    "pf-c-banner": true,
                    "pf-m-sticky": sticky,
                    [dispositionClass]: true,
                })}
            >
                <span class="pf-c-banner__icon" part="icon">
                    <i class=${iconClass} aria-hidden="true"></i>
                </span>
                <div class="pf-c-banner__content" part="content">
                    <slot></slot>
                    ${actionHref && actionLabel
                        ? html`<a part="action-link" href=${actionHref}>${actionLabel}</a>`
                        : null}
                </div>
                ${dismissKey
                    ? html`<button
                          part="dismiss-button"
                          class="pf-c-button ${dispositionClass}"
                          type="button"
                          aria-label=${msg("Dismiss banner", { id: "banner.dismiss.aria-label" })}
                          @click=${this.dismiss}
                      >
                          <i class="fas fa-times" aria-hidden="true"></i>
                      </button>`
                    : null}
            </div>`;
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-banner": Banner;
    }
}
