import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Markdown";
import { bound } from "@goauthentik/elements/decorators/bound";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

import { SidebarHelpToggleEvent } from "./events.js";

/**
 * A "Display documentation for this page" element.
 *
 * Based on the Patternfly "sidebar" pattern, this shows a vertically rotated button with a label to
 * indicate that it leads to documentation; when pressed, the button is replaced with the
 * documentation, rendered as a Markdown document.
 *
 * The SidebarHelp feature uses some fairly fiddly CSS to rotate the "Documentation" button in a way
 * that doesn't take up too much screen real-estate, because the rotation is purely visual; the
 * layout flow is still driven by the size of the button as if it were horizontal. Using the
 * SidebarHelp means enabling a special SidebarHelpController on the container to adjust the width
 * of the container to the *height* of the button when the button is rotated into place.
 *
 * @element ak-sidebar-help
 *
 * The events fired by this component are not for general use.
 */

@customElement("ak-sidebar-help")
export class SidebarHelp extends AKElement {
    static get styles() {
        return [
            PFCard,
            PFButton,
            PFDisplay,
            PFFlex,
            PFSpacing,
            css`
                .vert {
                    transform-origin: bottom left;
                    translate: 0 -100%;
                    rotate: 90deg;
                }
                .ak-fit-text {
                    width: fit-content;
                }
            `,
        ];
    }

    /*
     * @attr The content of the documentation to be shown
     */
    @property({ attribute: false })
    content: string = "";

    /*
     * @attr The style to use when the content is visible
     */
    @property({ attribute: "active-style" })
    activeStyle = "pf-m-width-25";

    /*
     * @attr The label on the button when the content is not visible.
     */
    @property()
    label: string = msg("Documentation");

    @state()
    showing = false;

    @query("#toggle")
    button!: HTMLButtonElement;

    @bound
    toggle() {
        this.showing = !this.showing;
    }

    render() {
        if (!this.showing) {
            return html`<button
                type="button"
                id="toggle"
                class="pf-c-button pf-m-primary vert"
                @click=${this.toggle}
            >
                ${this.label}
            </button>`;
        }

        return html`
            <div class="pf-c-card">
                <div class="pf-u-display-flex pf-u-justify-content-flex-end">
                    <button
                        type="button"
                        class=" pf-c-button pf-m-secondary pf-u-m-md ak-fit-text"
                        @click=${this.toggle}
                    >
                        ${msg("Hide")}
                    </button>
                </div>
                <div class="pf-c-card__body">
                    <ak-markdown .md=${this.content} meta="applications/index.md"></ak-markdown>
                </div>
            </div>
        `;
    }

    updated() {
        this.dispatchEvent(new SidebarHelpToggleEvent(this));
    }
}
