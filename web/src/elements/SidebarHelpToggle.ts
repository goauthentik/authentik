import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Markdown";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFSpacing from "@patternfly/patternfly/utilities/Spacing/spacing.css";

import { bound } from "./decorators/bound";

@customElement("ak-sidebar-help-toggle")
export class ToggledSidebarHelp extends AKElement {
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
                    rotate: 90deg;
                    translate: 0 -100%;
                }
                .ak-fit-text {
                    width: fit-content;
                }
            `,
        ];
    }

    @property({ attribute: false })
    content: string = "";

    @property({ attribute: "active-style" })
    activeStyle = "pf-m-width-25";

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
            // eslint-disable-next-line wc/no-self-class
            this.classList.remove(this.activeStyle);
            // eslint-disable-next-line wc/no-self-class
            this.classList.add("pf-m-width-default");
            return html`<button
                type="button"
                id="toggle"
                class="pf-c-button pf-m-primary vert"
                @click=${this.toggle}
            >
                ${this.label}
            </button>`;
        }

        // eslint-disable-next-line wc/no-self-class
        this.classList.remove("pf-m-width-default");
        // eslint-disable-next-line wc/no-self-class
        this.classList.add(this.activeStyle);
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
        requestAnimationFrame(() => {
            if (this.showing) {
                this.style.removeProperty("width");
            } else {
                if (this.button) {
                    const { width } = this.button.getBoundingClientRect();
                    this.style.setProperty("width", `${width}px`);
                }
            }
        });
    }
}
