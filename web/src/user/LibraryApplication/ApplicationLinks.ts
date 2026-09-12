import "#elements/AppIcon";

import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";

import { AlignEnum, type ApplicationLinks as ApplicationLinksConfig } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, html, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

/**
 * Beyond this, remaining links fold into a counter.
 *
 * Roughly two rows on the narrowest card, which also carries the copy button.
 * The row wraps, so nothing below this cap is hidden; the cap exists only so one
 * misconfigured application cannot stretch its whole grid row, every card in it
 * matching the tallest.
 */
const MAX_VISIBLE = 8;

/** Every link gets an icon; this one stands in when none is configured. */
const DEFAULT_ICON = "fa://fa-link";

/** How long the copy button stays in its resolved state before reverting. */
const FEEDBACK_MS = 2000;

type CopyState = "idle" | "copied" | "failed";

/**
 * Only http and https are accepted. Defense in depth: the serializer rejects
 * other schemes, but a value could predate the validator or arrive from a
 * blueprint.
 */
function isSafeURL(candidate: string): boolean {
    try {
        const { protocol } = new URL(candidate);
        return protocol === "https:" || protocol === "http:";
    } catch {
        return false;
    }
}

/**
 * The address a native client is pointed at, derived from the application launch
 * URL and never hand-entered, so it cannot contradict the real link. Includes the
 * port only when it is not the scheme's default.
 */
function connectionAddress(launchUrl: string): string | null {
    try {
        const url = new URL(launchUrl);
        if (url.protocol !== "https:" && url.protocol !== "http:") return null;
        return url.port
            ? `${url.protocol}//${url.hostname}:${url.port}`
            : `${url.protocol}//${url.hostname}`;
    } catch {
        return null;
    }
}

/**
 * Copy through the legacy command, in the shape iOS accepts.
 *
 * The usual recipe — a hidden `textarea`, `select()`, `execCommand` — copies
 * nothing on iOS, which ignores `select()` on a field it considers non-editable.
 * A contentEditable element with an explicit Range works on every engine. The
 * previous selection is restored so the page is left as it was found.
 */
function legacyCopy(text: string): boolean {
    const carrier = document.createElement("div");
    carrier.contentEditable = "true";
    carrier.textContent = text;
    // Off-screen but still rendered: `display: none` or `visibility: hidden`
    // would make the range unselectable and the copy a no-op.
    carrier.style.cssText =
        "position:fixed;inset-block-start:0;inset-inline-start:0;" +
        "opacity:0;pointer-events:none;white-space:pre;user-select:text;";
    document.body.append(carrier);

    const selection = window.getSelection();
    const previous = selection?.rangeCount ? selection.getRangeAt(0) : null;
    const range = document.createRange();
    range.selectNodeContents(carrier);
    selection?.removeAllRanges();
    selection?.addRange(range);

    let copied = false;
    try {
        copied = document.execCommand("copy");
    } catch {
        copied = false;
    }

    selection?.removeAllRanges();
    if (previous) selection?.addRange(previous);
    carrier.remove();
    return copied;
}

/**
 * Additional links and connection address shown under an application card.
 *
 * Everything it renders comes from the application's own `applicationLinks`
 * block: two switches, an optional heading, an alignment and the links. With the
 * block absent or both switches off, the component renders nothing and the
 * dashboard is unchanged down to the card geometry.
 *
 * Rendered as a SIBLING of the launch anchor, never nested: an anchor inside an
 * anchor is invalid HTML, and activating a link must not also launch the
 * application.
 */
@customElement("ak-library-app-links")
export class ApplicationLinks extends AKElement {
    @property({ type: Object, attribute: false })
    config?: ApplicationLinksConfig;

    @property({ type: String, attribute: "app-name" })
    appName = "";

    @property({ type: String, attribute: "launch-url" })
    launchUrl = "";

    @state()
    private copyState: CopyState = "idle";

    #feedbackTimer = -1;

    disconnectedCallback(): void {
        clearTimeout(this.#feedbackTimer);
        super.disconnectedCallback();
    }

    #resolve(state: CopyState): void {
        this.copyState = state;
        clearTimeout(this.#feedbackTimer);
        this.#feedbackTimer = window.setTimeout(() => {
            this.copyState = "idle";
        }, FEEDBACK_MS);
    }

    /**
     * The address is resolved during render and handed in, never looked up here.
     *
     * Safari only honours a clipboard write while it is still processing the
     * gesture that triggered it. Any `await` — or any work that yields — before
     * `writeText` loses that context and the write is refused without an error
     * the user can see. So: no async work ahead of the call, and the promise is
     * handled only afterwards.
     */
    #copy = (address: string) => {
        if (navigator.clipboard?.writeText) {
            navigator.clipboard.writeText(address).then(
                () => this.#resolve("copied"),
                // Denied permission, or an insecure context that advertises the
                // API without honouring it. The legacy path still works there.
                () => this.#resolve(legacyCopy(address) ? "copied" : "failed"),
            );
            return;
        }
        this.#resolve(legacyCopy(address) ? "copied" : "failed");
    };

    static styles = [
        css`
            :host {
                display: block;

                /* Every size in the footer derives from these, so a glyph, an
                   uploaded image and the overflow counter cannot drift apart.

                   32px is not a taste: it is the largest size that fits four
                   links on one line of the NARROWEST card. A card is at least
                   10rem wide, less 2 x 0.5rem of padding, so 144px of content;
                   four pills plus three 4px gaps must hold in it, which caps a
                   pill at (144 - 12) / 4 = 33px. At 39px the fourth icon was
                   clipped. */
                --ak-link-size: 32px;
                --ak-link-glyph: 1.25rem;
                /* Share of the square an image fills. A glyph covers roughly
                   three quarters of its em box, so 100% would make logos look
                   bigger than the icon font; this sits between the two. It is a
                   ratio, not a size: it stays put when the sizes change. */
                --ak-link-image-scale: 88%;
            }
            :host([hidden]) {
                display: none;
            }

            .footer {
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                justify-content: center;
                gap: 0.125rem;
                min-height: var(--app-links-height);
                padding-block: var(--pf-global--spacer--xs);
                padding-inline: var(--pf-global--spacer--sm);
                border-block-start: 1px solid var(--pf-global--BorderColor--100);
                /* The card overlays its icon absolutely: an opaque background
                   keeps it from showing through the row. */
                background: var(--pf-c-card--BackgroundColor);
            }

            .heading {
                font-size: var(--pf-global--FontSize--xs);
                color: var(--pf-global--Color--200);
                line-height: 1.2;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            /* Wraps rather than scrolls. A scrolling row hides links behind an
               affordance nothing announces — the fifth icon was simply cut off,
               with no hint that it existed. Wrapping shows everything and costs
               only height, which the card can give. */
            .row {
                display: flex;
                flex-wrap: wrap;
                align-items: center;
                justify-content: center;
                gap: var(--pf-global--spacer--xs);
                row-gap: 0.125rem;
            }

            /* The heading alone moves. The links stay centered whatever the
               setting: a row of icons reads as one block, and shifting it to an
               edge only unbalances the card.

               Physical values, not logical: an administrator sets this once for
               every viewer, so it must not mirror itself per locale. */
            :host([data-align="left"]) .heading {
                text-align: left;
            }
            :host([data-align="center"]) .heading {
                text-align: center;
            }
            :host([data-align="right"]) .heading {
                text-align: right;
            }

            /* Same treatment as the card menu button. */
            a,
            .copy,
            .more {
                flex: 0 0 auto;
                display: grid;
                place-items: center;
                width: var(--ak-link-size);
                height: var(--ak-link-size);
                border: none;
                border-radius: var(--pf-global--BorderRadius--sm);
                background: none;
                padding: 0;
                color: var(--pf-global--Color--200);
                text-decoration: none;
                transition:
                    color 120ms ease-in-out,
                    background-color 120ms ease-in-out;
            }
            .more {
                /* Slightly under the glyph size: text of the same nominal size
                   reads larger than an icon. */
                font-size: calc(var(--ak-link-glyph) * 0.85);
            }
            .copy {
                cursor: pointer;
                font-size: calc(var(--ak-link-glyph) * 0.85);
            }
            .copy.copied {
                color: var(--pf-global--success-color--100);
            }
            .copy.failed {
                color: var(--pf-global--danger-color--100);
            }

            /* Hover styling only where hovering exists. On iOS a first tap on a
               hover-styled element is sometimes spent simulating the hover,
               which would cost the user a second tap to actually copy. */
            @media (hover: hover) {
                a:hover,
                .copy:hover {
                    color: var(--pf-global--Color--100);
                    background-color: var(--pf-c-card--m-flat--BorderColor);
                }
                a:hover ak-app-icon::part(image) {
                    filter: none;
                    opacity: 1;
                }
            }
            a:focus-visible,
            .copy:focus-visible {
                color: var(--pf-global--Color--100);
                outline: 2px solid var(--ak-accent);
                outline-offset: 1px;
            }
            a:focus-visible ak-app-icon::part(image) {
                filter: none;
                opacity: 1;
            }

            /* The tooltip carries the address, which is no longer written out
               anywhere else. It must therefore reach touch users too: it is
               opened by the copy itself, not by hover alone.

               Anchored to the button, not to the footer. Anchoring it to the
               footer and centring it there looked right on a 200px card and
               fell apart in row view, where the footer spans a whole column and
               the tooltip drifted far from the button it describes. The row no
               longer scrolls — it wraps — so nothing clips it here any more. */
            .tip-anchor {
                position: relative;
                flex: 0 0 auto;
                display: grid;
                place-items: center;
            }
            .tip {
                position: absolute;
                inset-block-end: calc(100% + 0.25rem);
                inset-inline-start: 50%;
                translate: -50% 0;
                z-index: 1;
                max-width: min(18rem, 60vw);
                padding: 0.25rem 0.5rem;
                border-radius: var(--pf-global--BorderRadius--sm);
                background: var(--pf-global--BackgroundColor--dark-400, #151515);
                color: var(--pf-global--Color--light-100, #fff);
                font-size: var(--pf-global--FontSize--xs);
                line-height: 1.3;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                opacity: 0;
                visibility: hidden;
                transition:
                    opacity 120ms ease-in-out,
                    visibility 120ms;
            }
            /* Failure is the one case where the address must be readable and
               selectable, since nothing else on the card shows it. */
            .tip.failed {
                white-space: normal;
                user-select: text;
                -webkit-user-select: text;
            }
            /* Opened by the copy itself — the only path a touch screen has. */
            .tip.open,
            /* Keyboard users, on every platform. */
            .tip-anchor:focus-within .tip {
                opacity: 1;
                visibility: visible;
            }
            @media (hover: hover) {
                .tip-anchor:hover .tip {
                    opacity: 1;
                    visibility: visible;
                }
            }

            /* One square for both render paths. ak-app-icon centers with
               place-content, which does not center a single flex item on the
               block axis, hence the explicit alignment. */
            ak-app-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                width: var(--ak-link-glyph);
                height: var(--ak-link-glyph);
                --icon-height: var(--ak-link-glyph);
                --icon-border: 0;
            }
            ak-app-icon::part(icon) {
                display: block;
                line-height: 1;
                filter: none;
            }
            ak-app-icon::part(image) {
                width: var(--ak-link-image-scale);
                height: var(--ak-link-image-scale);
                object-fit: contain;
                /* Vendor marks are solid blocks of color beside monochrome
                   glyphs. Muting them at rest keeps the row reading as one set;
                   color returns on hover, like the surrounding icons. */
                filter: grayscale(1);
                opacity: 0.7;
                transition:
                    filter 120ms ease-in-out,
                    opacity 120ms ease-in-out;
            }
        `,
    ];

    private renderCopy(address: string): TemplateResult {
        const { copyState } = this;

        return html`<button
            class=${classMap({ copy: true, [copyState]: copyState !== "idle" })}
            part="connection-copy"
            type="button"
            @click=${() => this.#copy(address)}
            aria-label=${msg(str`Copy the address of ${this.appName}`, {
                id: "library.connection.copy.aria-label",
                desc: "Screen reader label for the copy address button",
            })}
        >
            <i
                class="fas ${copyState === "copied"
                    ? "fa-check"
                    : copyState === "failed"
                      ? "fa-exclamation-triangle"
                      : "fa-copy"}"
                aria-hidden="true"
            ></i>
        </button>`;
    }

    /**
     * Carries the address on hover and the outcome after a copy. On failure it
     * keeps showing the address, selectable, because nothing else on the card
     * writes it out any more — a silent clipboard error would otherwise leave the
     * user with nothing at all.
     */
    private renderTip(address: string): TemplateResult {
        const { copyState } = this;

        return html`<span
            class=${classMap({
                tip: true,
                open: copyState !== "idle",
                failed: copyState === "failed",
            })}
            part="connection-tooltip"
            role="status"
            aria-live="polite"
            >${copyState === "copied"
                ? msg("Address copied", {
                      id: "library.connection.copy.done",
                      desc: "Confirmation shown in a tooltip once the application's web address has been put on the clipboard.",
                  })
                : address}</span
        >`;
    }

    private renderLink(link: { label: string; url: string; icon?: string }): TemplateResult {
        return html`<a
            href=${link.url}
            target="_blank"
            rel="noopener noreferrer"
            part="application-link"
            title=${link.label}
            aria-label=${msg(str`${link.label} — ${this.appName}`, {
                id: "library.application-links.aria-label",
                desc: "Screen reader label for an additional application link",
            })}
        >
            <ak-app-icon
                size=${PFSize.Small}
                name=${link.label}
                icon=${link.icon || DEFAULT_ICON}
            ></ak-app-icon>
        </a>`;
    }

    render() {
        const config = this.config;
        const usable =
            config?.enabled && config.links
                ? config.links.filter((link) => link.label && isSafeURL(link.url))
                : [];
        const address = config?.address ? connectionAddress(this.launchUrl) : null;

        // Nothing configured: render nothing at all, so an application that does
        // not use the block is unchanged down to the card geometry.
        this.hidden = !address && usable.length === 0;
        if (this.hidden) return nothing;

        this.dataset.align = config?.align ?? AlignEnum.Center;

        const visible = usable.slice(0, MAX_VISIBLE);
        const overflow = usable.length - visible.length;
        const heading = config?.title?.trim();

        return html`<div class="footer" part="links-footer">
            ${heading
                ? html`<div class="heading" part="links-heading" title=${heading}>${heading}</div>`
                : nothing}
            <div class="row" part="application-links">
                ${visible.map((link) => this.renderLink(link))}
                ${overflow > 0
                    ? html`<span
                          class="more"
                          title=${msg(str`${overflow} more`, {
                              id: "library.application-links.overflow.tooltip",
                              desc: "Tooltip on the counter standing in for links beyond the display limit. The placeholder is a number, as in '3 more'.",
                          })}
                          >+${overflow}</span
                      >`
                    : nothing}
                ${address
                    ? html`<span class="tip-anchor"
                          >${this.renderCopy(address)}${this.renderTip(address)}</span
                      >`
                    : nothing}
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-app-links": ApplicationLinks;
    }
}
