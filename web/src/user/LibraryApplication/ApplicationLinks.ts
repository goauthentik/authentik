import "#elements/AppIcon";

import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import { WithSession } from "#elements/mixins/session";

import { ApplicationLink } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, html, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

/** Beyond this, remaining links fold into a counter. */
const MAX_VISIBLE = 5;

/** Every link gets an icon; this one stands in when none is configured. */
const DEFAULT_ICON = "fa://fa-link";

interface ConnectionInfo {
    /** Scheme and host: what the copy button puts on the clipboard. */
    address: string;
    /** Host alone: what is displayed, to save width. */
    host: string;
    /** Empty when the URL uses the scheme's default port. */
    port: string;
}

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
 * Derived from the application launch URL, never hand-entered, so the
 * displayed address cannot contradict the real link.
 */
function connectionInfo(launchUrl: string): ConnectionInfo | null {
    try {
        const url = new URL(launchUrl);
        if (url.protocol !== "https:" && url.protocol !== "http:") return null;
        return {
            address: `${url.protocol}//${url.hostname}`,
            host: url.hostname,
            port: url.port,
        };
    } catch {
        return null;
    }
}

/**
 * Connection address and additional links shown under an application card.
 *
 * Both blocks are independent and off by default, driven by
 * `UIConfig.enabledFeatures`. With neither enabled the component renders
 * nothing and the dashboard is unchanged down to the card geometry.
 *
 * Rendered as a SIBLING of the launch anchor, never nested: an anchor inside
 * an anchor is invalid HTML, and activating a link must not also launch the
 * application.
 */
@customElement("ak-library-app-links")
export class ApplicationLinks extends WithSession(AKElement) {
    @property({ type: Array, attribute: false })
    links: ApplicationLink[] = [];

    @property({ type: String, attribute: "app-name" })
    appName = "";

    @property({ type: String, attribute: "launch-url" })
    launchUrl = "";

    @state()
    private copied = false;

    private copyAddress = async (): Promise<void> => {
        const info = connectionInfo(this.launchUrl);
        if (!info) return;
        const full = info.port ? `${info.address}:${info.port}` : info.address;
        try {
            await navigator.clipboard.writeText(full);
            this.copied = true;
            setTimeout(() => {
                this.copied = false;
            }, 1600);
        } catch {
            // Insecure context or denied permission: the text stays
            // selectable, so the feature degrades instead of breaking.
        }
    };

    static styles = [
        css`
            :host {
                display: block;
            }
            :host([hidden]) {
                display: none;
            }

            /* Without links the row collapses and the address block takes the
               whole footer, staying centered. The card keeps its height. */
            .footer.no-links .links {
                display: none;
            }
            .footer.no-links .info {
                min-height: calc(var(--app-address-height) + var(--app-links-height));
            }

            .info {
                box-sizing: border-box;
                display: grid;
                place-content: center;
                min-height: var(--app-address-height);
                padding-inline: var(--pf-global--spacer--sm);
                border-block-start: 1px solid var(--pf-global--BorderColor--100);
                font-size: var(--pf-global--FontSize--sm);
                user-select: text;
                -webkit-user-select: text;
            }
            .info .line {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: var(--pf-global--spacer--xs);
                white-space: nowrap;
                min-width: 0;
            }
            /* flex: 0 1 auto — the address takes only its own width, which is
               what actually centers the address and its button together. */
            .info .value {
                flex: 0 1 auto;
                min-width: 0;
                overflow: hidden;
                text-overflow: ellipsis;
                color: var(--pf-global--Color--200);
            }

            .links {
                box-sizing: border-box;
                display: flex;
                flex-wrap: nowrap;
                align-items: center;
                justify-content: center;
                gap: var(--pf-global--spacer--sm);
                min-height: var(--app-links-height);
                border-block-start: 1px solid var(--pf-global--BorderColor--100);
                /* The card overlays its icon absolutely: an opaque background
                   keeps it from showing through the row. */
                background: var(--pf-c-card--BackgroundColor);
            }

            /* Every size in the footer derives from these three values, so
               a glyph, an uploaded image and the overflow counter cannot
               drift apart. */
            :host {
                --ak-link-size: 26px;
                --ak-link-copy-size: 18px;
                --ak-link-glyph: 1rem;
                /* Share of the square an image fills. A glyph covers
                   roughly three quarters of its em box, so a value of
                   100% would make logos look bigger than the icon font;
                   this sits between the two. */
                --ak-link-image-scale: 88%;
            }

            /* Same treatment as the card menu button. */
            a,
            .copy,
            .more {
                display: grid;
                place-items: center;
                border: none;
                border-radius: var(--pf-global--BorderRadius--sm);
                background: none;
                color: var(--pf-global--Color--200);
                text-decoration: none;
                transition:
                    color 120ms ease-in-out,
                    background-color 120ms ease-in-out;
            }
            a,
            .more {
                width: var(--ak-link-size);
                height: var(--ak-link-size);
            }
            .more {
                /* Slightly under the glyph size: text of the same nominal
                   size reads larger than an icon. */
                font-size: calc(var(--ak-link-glyph) * 0.85);
            }
            .copy {
                flex: 0 0 auto;
                width: var(--ak-link-copy-size);
                height: var(--ak-link-copy-size);
                padding: 0;
                cursor: pointer;
                font-size: calc(var(--ak-link-copy-size) * 0.6);
            }
            a:hover,
            a:focus-visible,
            .copy:hover,
            .copy:focus-visible {
                color: var(--pf-global--Color--100);
                background-color: var(--pf-c-card--m-flat--BorderColor);
                outline: none;
            }
            a:focus-visible,
            .copy:focus-visible {
                outline: 2px solid var(--ak-accent);
                outline-offset: 1px;
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
                   glyphs. Muting them at rest keeps the row reading as one
                   set; color returns on hover, like the surrounding icons. */
                filter: grayscale(1);
                opacity: 0.7;
                transition:
                    filter 120ms ease-in-out,
                    opacity 120ms ease-in-out;
            }
            a:hover ak-app-icon::part(image),
            a:focus-visible ak-app-icon::part(image) {
                filter: none;
                opacity: 1;
            }
        `,
    ];

    private renderConnection(): TemplateResult | typeof nothing {
        const info = connectionInfo(this.launchUrl);
        if (!info) return nothing;
        return html`<div class="info" part="connection-info">
            <div class="line">
                <span class="value" title=${info.address}>${info.host}</span>
                <button
                    class="copy"
                    part="connection-copy"
                    type="button"
                    @click=${this.copyAddress}
                    title=${this.copied
                        ? msg("Copied", { id: "library.connection.copy.done" })
                        : msg("Copy address", { id: "library.connection.copy.tooltip" })}
                    aria-label=${msg(str`Copy the address of ${this.appName}`, {
                        id: "library.connection.copy.aria-label",
                        desc: "Screen reader label for the copy address button",
                    })}
                >
                    <i class="fas ${this.copied ? "fa-check" : "fa-copy"}" aria-hidden="true"></i>
                </button>
            </div>
        </div>`;
    }

    private renderLink(link: ApplicationLink): TemplateResult {
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
        const { applicationLinks, applicationAddress } = this.uiConfig.enabledFeatures;

        const usable = applicationLinks
            ? this.links.filter((link) => link.label && isSafeURL(link.url))
            : [];
        const address = applicationAddress ? this.renderConnection() : nothing;

        // Both features off: render nothing at all, so a dashboard that does
        // not use them is unchanged down to the card geometry.
        this.hidden = address === nothing && usable.length === 0;
        if (this.hidden) return nothing;

        const visible = usable.slice(0, MAX_VISIBLE);
        const overflow = usable.length - visible.length;

        return html`<div class="footer ${usable.length ? "" : "no-links"}">
            ${address}
            <div class="links" part="application-links">
                ${visible.map((link) => this.renderLink(link))}
                ${overflow > 0
                    ? html`<span
                          class="more"
                          title=${msg(str`${overflow} more`, {
                              id: "library.application-links.overflow.tooltip",
                          })}
                          >+${overflow}</span
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
