import "#elements/Spinner";

import Styles from "./EmptyState.styles";

import FAIcons from "#elements/Icons_impl/Icons.styles";
import { WithSlottedContentCheck, Zero } from "#elements/mixins/slotted-content-check";
import { SlottedTemplateResult, Spread } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, LitElement, render } from "lit";
import { property } from "lit/decorators.js";

/**
 * @element ak-empty-state
 * @class EmptyState
 *
 * A component for displaying empty states with optional icons, headings, body text, and actions.
 * Follows PatternFly design patterns for empty state presentations.
 *
 * ## Slots
 *
 * @slot - The main heading text for the empty state
 * @slot body - Descriptive text explaining the empty state or what the user can do
 * @slot primary - Primary action buttons or other interactive elements
 *
 */

export class EmptyState extends WithSlottedContentCheck(LitElement) {
    static readonly styles = [Styles, FAIcons, Zero];

    @property({ type: String })
    public icon = "";

    @property({ type: Boolean, reflect: true })
    public loading = false;

    @property({ type: Boolean, reflect: true, attribute: "default-label" })
    public defaultLabel = false;

    @property({ type: Boolean, attribute: "full-height" })
    public fullHeight = false;

    public role = "status";

    willUpdate() {
        if (this.defaultLabel && this.querySelector("span:not([slot])") === null) {
            render(html`<span>${msg("Loading")}</span>`, this);
        }
    }

    get localAriaLabel() {
        const result = this.querySelector("span:not([slot])");
        return result instanceof HTMLElement ? result.innerText || undefined : undefined;
    }

    renderIcon() {
        return this.loading || this.defaultLabel
            ? html`<ak-spinner size="xl"></ak-spinner>`
            : html`<i
                  class="pf-icon fa ${this.icon || "fa-question-circle"}"
                  aria-hidden="true"
              ></i>`;
    }

    render() {
        const hide = this.provideContentHider();

        return html` <div part="empty-state">
            <div part="content">
                <div part="icon">${this.renderIcon()}</div>
                <h1 part="heading" class=${hide("heading")}>
                    <slot @slotchange=${this.checkForContent}></slot>
                </h1>
                <div part="body" class=${hide("body")}>
                    <slot name="body" @slotchange=${this.checkForContent}></slot>
                </div>
                <div part="primary" class=${hide("primary")}>
                    <slot name="primary" @slotchange=${this.checkForContent}></slot>
                </div>
            </div>
        </div>`;
    }
}

type ContentValue = SlottedTemplateResult | undefined;

export type EmptyStateProps = Partial<
    Pick<EmptyState, "icon" | "loading" | "defaultLabel" | "fullHeight">
>;

export interface EmptyStateContentProps {
    heading?: SlottedTemplateResult;
    body?: SlottedTemplateResult;
    primary?: SlottedTemplateResult;
}

/**
 * Generate `<ak-empty-state>` programmatically
 *
 * @param properties - properties to apply to the component.
 * @param content - strings or TemplateResults for the slots in `<ak-empty-state>`
 * @returns TemplateResult for the ak-empty-state element
 *
 */
export function akEmptyState(
    properties: EmptyStateProps = {},
    content: EmptyStateContentProps = {},
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

    return html`<ak-empty-state ${spread(properties as Spread)}>${items}</ak-empty-state>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-empty-state": EmptyState;
    }
}
