/**
 * @file `<ak-truncate>` — pixel-aware, structure-aware text truncation.
 *
 * Measures the host's rendered width and font, then truncates the source text so
 * its meaningful parts survive. The source is the `value` property or, when that
 * is unset, the element's slotted text content. Re-truncates on resize and once
 * web fonts settle. Framework-minimal: extends `LitElement` directly and takes
 * `lit` as an optional peer dependency.
 */

import { Truncator } from "../internal/primitives.js";
import { createCanvasMeasurer, type Measurer } from "../measurer.js";
import { TruncationResizeObserver } from "../resize-observer.js";

import { css, html, LitElement, type PropertyValues, TemplateResult } from "lit";
import { html as staticHTML, unsafeStatic } from "lit-html/static.js";
import { property, state } from "lit/decorators.js";

/**
 * The kind of value being truncated, selecting the structure-aware strategy.
 */
export type TruncateKind =
    | "url"
    | "hash"
    | "uuid"
    | "mac-address"
    | "ip-address"
    | "email"
    | "user-agent"
    | "string";

export abstract class AKTruncateBase extends LitElement {
    public static styles = css`
        :host {
            display: block;
            overflow: hidden;
        }

        span {
            white-space: nowrap;
        }

        /* The slot only carries the source text; it is never rendered. */
        slot {
            display: none;
        }
    `;

    declare ["constructor"]: typeof AKTruncateBase;

    /**
     * A single OffscreenCanvas shared across every instance; `measureText` only
     * depends on `ctx.font`, which we set synchronously per truncation pass.
     */
    protected static canvas: OffscreenCanvas | null = null;

    protected static measurer(font: string): Measurer {
        this.canvas ??= new OffscreenCanvas(0, 0);

        return createCanvasMeasurer(this.canvas, font);
    }

    /**
     * The text to truncate. Takes precedence over slotted content.
     */
    @property({ type: String })
    public value = "";

    protected abstract truncator: Truncator;

    @property({ type: String })
    public ellipsis = "…";

    @state()
    protected display = "";

    /**
     * Text captured from the slot, used as the source when `value` is unset.
     */
    @state()
    protected slotText = "";

    protected width = 0;

    /**
     * The source text: the `value` property, or the slotted text when `value` is
     * empty.
     */
    protected get source(): string {
        return this.value || this.slotText;
    }

    protected resizeListener = (width: number) => {
        if (width === this.width) return;

        this.width = width;
        this.truncate();
    };

    protected slotListener = (event: Event) => {
        const slot = event.target as HTMLSlotElement;
        const text = slot
            .assignedNodes({ flatten: true })
            .map((node) => node.textContent ?? "")
            .join("")
            .trim();

        if (text === this.slotText) return;

        this.slotText = text;
        this.truncate();
    };

    public constructor() {
        super();

        this.classList.add("ak-c-truncate");
    }

    public override connectedCallback() {
        super.connectedCallback();

        TruncationResizeObserver.shared.observe(this, this.resizeListener);

        // Web fonts change glyph metrics; re-truncate once they settle.
        this.ownerDocument.fonts.ready.then(() => this.truncate());
    }

    public override disconnectedCallback() {
        super.disconnectedCallback();

        TruncationResizeObserver.shared.unobserve(this);
    }

    protected override updated(changed: PropertyValues<this>) {
        super.updated(changed);

        if (changed.has("value") || changed.has("ellipsis")) {
            this.truncate();
        }
    }

    /**
     * Recompute the displayed text for the current width, font, and source. Runs
     * regardless of on-screen state, so off-screen rows are already truncated and
     * don't reflow when scrolled into view.
     */
    protected truncate = () => {
        const source = this.source;

        if (!source) {
            this.display = "";

            return;
        }

        // Keep the last computed text until we have a width to measure against,
        // rather than flashing back to the full value.
        if (this.width <= 0) return;

        const measure = this.constructor.measurer(getComputedStyle(this).font);

        this.display = this.truncator(source, {
            maxWidth: this.width,
            measure,
            ellipsis: this.ellipsis,
        });
    };

    protected override render() {
        const source = this.source;

        return html`<span part="text" title=${source}>${this.display || source}</span>
            <slot @slotchange=${this.slotListener}></slot>`;
    }
}

export interface TruncateFCProps {
    ellipsis?: string;
    fallback?: string;
}

export type TruncateFC = (
    input: string | undefined | null,
    props?: TruncateFCProps,
) => TemplateResult | null;

export function createTruncatorFC(ComponentConstructor: CustomElementConstructor): TruncateFC {
    const tagName = window.customElements.getName(ComponentConstructor);

    if (!tagName) {
        throw new Error(
            `Component ${ComponentConstructor.name} is not registered as a custom element.`,
        );
    }

    return (input, { ellipsis = "…", fallback = "-" } = {}) => {
        if (!input) {
            if (fallback === null) {
                return null;
            }

            return html`<div class="ak-c-truncate ak-m-fallback">${fallback}</div>`;
        }

        return staticHTML`<${unsafeStatic(tagName)} .ellipsis=${ellipsis} .fallback=${fallback}>${input}</${unsafeStatic(tagName)}>`;
    };
}
