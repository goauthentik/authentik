import "#elements/Spinner";

import { PFSize } from "#common/enums";

import { AKElement } from "#elements/Base";
import { type SlottedTemplateResult, type Spread } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { css, html, nothing, render } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * Props for the EmptyState component
 */
export interface IEmptyState {
    /** Font Awesome icon class (e.g., "fa-user", "fa-folder") to display */
    icon?: string;

    /** When true, will automatically show the loading spinner.  Overrides `icon`. */
    loading?: boolean;

    /**
     * When true, will automatically fill the header with the "Loading" message and show the loading
     * spinner. Overrides 'loading'.
     */
    defaultLabel?: boolean;

    /** Whether the empty state should take up the full height of its container */
    fullHeight?: boolean;
}

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
@customElement("ak-empty-state")
export class EmptyState extends AKElement implements IEmptyState {
    @property({ type: String })
    public icon = "";

    @property({ type: Boolean, reflect: true })
    public loading = false;

    @property({ type: Boolean, reflect: true, attribute: "default-label" })
    public defaultLabel = false;

    @property({ type: Boolean, attribute: "full-height" })
    public fullHeight = false;

    public role = "status";

    static styles = [
        PFBase,
        PFEmptyState,
        PFTitle,
        css`
            i.pf-c-empty-state__icon {
                height: var(--pf-global--icon--FontSize--2xl);
                line-height: var(--pf-global--icon--FontSize--2xl);
            }
        `,
    ];

    willUpdate() {
        if (this.defaultLabel && this.querySelector("span:not([slot])") === null) {
            render(html`<span>${msg("Loading")}</span>`, this);
        }
    }

    get localAriaLabel() {
        const result = this.querySelector("span:not([slot])");
        return result instanceof HTMLElement ? result.innerText || undefined : undefined;
    }

    render() {
        const hasHeading = this.hasSlotted(null);
        const loading = this.loading || this.defaultLabel;
        const classes = {
            "pf-c-empty-state": true,
            "pf-m-full-height": this.fullHeight,
        };

        return html`<div aria-label=${this.localAriaLabel ?? nothing} class="${classMap(classes)}">
            <div class="pf-c-empty-state__content">
                ${loading
                    ? html`<div part="spinner" class="pf-c-empty-state__icon">
                          <ak-spinner size=${PFSize.XLarge}></ak-spinner>
                      </div>`
                    : html`<i
                          part="icon"
                          class="pf-icon fa ${this.icon ||
                          "fa-question-circle"} pf-c-empty-state__icon"
                          aria-hidden="true"
                      ></i>`}
                ${hasHeading
                    ? html` <h1 part="heading" class="pf-c-title pf-m-lg" id="empty-state-heading">
                          <slot></slot>
                      </h1>`
                    : nothing}
                ${this.hasSlotted("body")
                    ? html` <div part="body" class="pf-c-empty-state__body">
                          <slot name="body"></slot>
                      </div>`
                    : nothing}
                ${this.hasSlotted("primary")
                    ? html` <div part="primary" class="pf-c-empty-state__primary">
                          <slot name="primary"></slot>
                      </div>`
                    : nothing}
            </div>
        </div>`;
    }
}

interface IEmptyStateContent {
    heading?: SlottedTemplateResult;
    body?: SlottedTemplateResult;
    primary?: SlottedTemplateResult;
}

type ContentKey = keyof IEmptyStateContent;
type ContentValue = SlottedTemplateResult | undefined;

/**
 * Generate `<ak-empty-state>` programmatically
 *
 * @param properties - properties to apply to the component.
 * @param content - strings or TemplateResults for the slots in `<ak-empty-state>`
 * @returns TemplateResult for the ak-empty-state element
 *
 */
export function akEmptyState(properties: IEmptyState = {}, content: IEmptyStateContent = {}) {
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
