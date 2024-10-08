import { PFSize } from "@goauthentik/common/enums.js";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Spinner";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFEmptyState from "@patternfly/patternfly/components/EmptyState/empty-state.css";
import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IEmptyState {
    icon?: string;
    loading?: boolean;
    fullHeight?: boolean;
    header?: string;
}

/**
 * @class EmptyState
 * @element ak-empty-state
 *
 * The EmptyState is an in-page element to indicate that something is either loading or unavailable.
 * When "loading" is true it displays a spinner, otherwise it displays a static icon. The default
 * icon is a question mark in a circle.
 *
 * @slot body - Optional low-priority text that appears beneath the state indicator.
 * @slot primary - Optional high-priority text that appears some distance between the state indicator.
 *
 * The layout of the component is always centered, and from top to bottom:
 *
 * ```
 *  icon or spinner
 *     header
 *      body
 *     primary
 * ```
 */
@customElement("ak-empty-state")
export class EmptyState extends AKElement implements IEmptyState {
    /**
     * The Font Awesome icon to display. Defaults to the � symbol.
     *
     * @attr
     */
    @property({ type: String })
    icon = "fa-question-circle";

    /**
     * Whether or not to show the spinner, or the end icon
     *
     * @attr
     */
    @property({ type: Boolean })
    loading = false;

    /**
     * If set, will attempt to occupy the full viewport.
     *
     * @attr
     */
    @property({ type: Boolean })
    fullHeight = false;

    /**
     * [Optional] If set, will display a message in large text beneath the icon
     *
     * @attr
     */
    @property()
    header?: string;

    static get styles(): CSSResult[] {
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

    render(): TemplateResult {
        return html`<div class="pf-c-empty-state ${this.fullHeight && "pf-m-full-height"}">
            <div class="pf-c-empty-state__content">
                ${this.loading
                    ? html`<div class="pf-c-empty-state__icon">
                          <ak-spinner size=${PFSize.XLarge}></ak-spinner>
                      </div>`
                    : html`<i
                          class="pf-icon fa ${this.icon} pf-c-empty-state__icon"
                          aria-hidden="true"
                      ></i>`}
                <h1 class="pf-c-title pf-m-lg">
                    ${this.loading && this.header === undefined ? msg("Loading") : this.header}
                </h1>
                <div class="pf-c-empty-state__body">
                    <slot name="body"></slot>
                </div>
                <div class="pf-c-empty-state__primary">
                    <slot name="primary"></slot>
                </div>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-empty-state": EmptyState;
    }
}
