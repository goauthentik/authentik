import { PFSize } from "@goauthentik/common/enums.js";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Spinner";
import { type SlottedTemplateResult, type Spread } from "@goauthentik/elements/types";
import { spread } from "@open-wc/lit-helpers";
import { component } from "haunted";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

/**
 * Interface defining the properties for the EmptyState component
 */
export interface IEmptyState {
    /** Font Awesome icon class (e.g., "fa-user", "fa-folder") to display */
    icon?: string;

    /** When true, will automatically show the loading spinner.  Overrides `icon`. */
    loading?: boolean;

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
 * @slot heading - The main heading text for the empty state
 * @slot body - Descriptive text explaining the empty state or what the user can do
 * @slot primary - Primary action buttons or other interactive elements
 *
 */
@customElement("ak-empty-state")
export class EmptyState extends AKElement implements IEmptyState {
    @property({ type: String })
    icon = "";

    @property({ type: Boolean })
    loading = false;

    @property({ type: Boolean, attribute: "full-height" })
    fullHeight = false;

    static get styles() {
        return [
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
    }

    render() {
        const hasHeading = this.hasSlotted(null);

        return html`<div
            class="pf-c-empty-state ${hasHeading
                ? html`aria-labelledby="empty-state-heading"`
                : ""} ${this.fullHeight && "pf-m-full-height"}"
        >
            <div class="pf-c-empty-state__content">
                ${this.loading
                    ? html`<div part="spinner" class="pf-c-empty-state__icon">
                          <ak-spinner size=${PFSize.XLarge}></ak-spinner>
                      </div>`
                    : this.icon
                      ? html`<i
                            part="icon"
                            class="pf-icon fa ${this.icon ||
                            "fa-question-circle"} pf-c-empty-state__icon"
                            aria-hidden="true"
                        ></i>`
                      : nothing}
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
 * Function to create `<ak-empty-state>` programmatically
 *
 * @param properties - properties to apply to the component.
 * @param content - strings or TemplateResults for the slots in `<ak-empty-state>`
 * @returns TemplateResult for the ak-empty-state element
 *
 */
export function akEmptyState(properties: IEmptyState = {}, content: IEmptyStateContent = {}) {
    const stringToSlot = (name: string, c: ContentValue) =>
        name === "heading" ? html`<span>${c}</span>` : html`<span slot=${name}>${c}</span>`;

    const stringToTemplate = (name: string, c: ContentValue) =>
        typeof c === "string" ? stringToSlot(name, c) : c;

    const items = Object.entries(content)
        .map(([name, content]) => stringToTemplate(name, content))
        .filter(Boolean);

    return html`<ak-empty-state ${spread(properties as Spread)}>${items}</ak-empty-state>`;
}

export const EmptyAndLoading = component(function () {
    return html`<ak-empty-state loading><span>${msg("Loading")}</span></ak-empty-state>`;
});

customElements.define("ak-empty-and-loading", EmptyAndLoading);

export function akEmptyAndLoading() {
    return html` <ak-empty-and-loading> </ak-empty-and-loading>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-empty-state": EmptyState;
        "ak-empty-and-loading": typeof EmptyAndLoading;
    }
}
