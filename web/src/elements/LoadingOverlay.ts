import "#elements/EmptyState";

import { AKElement } from "#elements/Base";
import Styles from "#elements/LoadingOverlay.css";
import { type SlottedTemplateResult, type Spread } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { spread } from "@open-wc/lit-helpers";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface ILoadingOverlay {
    /**
     * Whether this overlay should appear above all other overlays (z-index: 999)
     */
    topmost?: boolean;

    /**
     * Whether to show the loading spinner animation
     */
    noSpinner?: boolean;

    /**
     * Icon name to display instead of the default loading spinner
     */
    icon?: string | null;
}

/**
 * @element ak-loading-overlay
 * @class LoadingOverlay
 *
 * A component for for showing a loading message above a darkening background, in order
 * to pause interaction while dynamically importing a major component.
 *
 * ## Slots
 *
 * @slot - The main heading text for the loading state
 * @slot body - Descriptive text explaining the loading state
 *
 */
@customElement("ak-loading-overlay")
export class LoadingOverlay extends AKElement implements ILoadingOverlay {
    static styles = [Styles];

    // Do not camelize: https://www.merriam-webster.com/dictionary/topmost
    @property({ type: Boolean, attribute: "topmost" })
    public topmost = false;

    @property({ type: Boolean, attribute: "no-spinner", useDefault: true })
    public noSpinner = false;

    @property({ type: String, useDefault: true })
    public icon: string | null = null;

    render() {
        // Nested slots. Can get a little cognitively heavy, so be careful if you're editing here...
        return html`<ak-empty-state ?loading=${!this.noSpinner} icon=${ifPresent(this.icon)}>
            ${this.hasSlotted(null) ? html`<span><slot></slot></span>` : nothing}
            ${this.hasSlotted("body")
                ? html`<span slot="body"><slot name="body"></slot></span>`
                : nothing}
        </ak-empty-state>`;
    }
}

interface ILoadingOverlayContent {
    heading?: SlottedTemplateResult;
    body?: SlottedTemplateResult;
}

type ContentKey = keyof ILoadingOverlayContent;
type ContentValue = SlottedTemplateResult | undefined;

/**
 * Function to create `<ak-loading-overlay>` programmatically
 *
 * @param properties - properties to apply to the component.
 * @param content - strings or TemplateResults for the slots in `<ak-loading-overlay>`
 * @returns TemplateResult for the ak-loading-overlay element
 *
 */
export function akLoadingOverlay(
    properties: ILoadingOverlay = {},
    content: string | ILoadingOverlayContent = {},
) {
    // `heading` here is an Object.key of ILoadingOverlayContent, not the obsolete
    // slot-name.
    const stringToSlot = (name: string, c: ContentValue) =>
        name === "heading" ? html`<span>${c}</span>` : html`<span slot=${name}>${c}</span>`;

    const stringToTemplate = (name: string, c: ContentValue) =>
        typeof c === "string" ? stringToSlot(name, c) : c;

    const items = Object.entries(content)
        .map(([name, content]) => stringToTemplate(name, content))
        .filter(Boolean);

    return html`<ak-loading-overlay ${spread(properties as Spread)}>${items}</ak-loading-overlay>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-loading-overlay": LoadingOverlay;
    }
}
