import { AKElement } from "#elements/Base";
import { classList } from "#elements/directives/class-list";

import { css, html } from "lit";
import { property } from "lit/decorators.js";

import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";

const Style = css`
    slot {
        display: content;
    }

    [data-theme="dark"] {
        --pf-c-drawer__panel--BackgroundColor: var(--ak-dark-background);
    }

    .pf-c-drawer {
        /* TODO: Revisit this after native <dialog> modals are implemented. */
        --pf-c-drawer__content--ZIndex: auto;
    }

    .pf-c-drawer__body {
        display: flex;
        flex-flow: column;
    }

    .pf-c-drawer__content {
        --pf-c-drawer__content--BackgroundColor: transparent;
    }

    .pf-c-drawer {
        .pf-c-drawer__panel {
            background-color: var(--pf-c-drawer__panel--BackgroundColor);

            transition-behavior: allow-discrete;

            gap: var(--pf-global--spacer--sm);

            @media (width > 768px) {
                flex-flow: row;

                .pf-c-drawer__panel_content {
                    flex: 1 1 auto;
                    max-width: 33dvw;
                }
            }
        }
    }

    /* #region Dark Theme */
`;

export class Drawer extends AKElement {
    static readonly styles = [PFDrawer, Style];

    @property({ type: Boolean, reflect: true })
    public open = false;

    render() {
        const open = [(this.open && "pf-m-expanded") || "pf-m-collapsed"];

        return html`
            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer ${classList(open)}" id="flow-drawer">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                <slot></slot>
                            </div>
                        </div>
                        <div class="pf-c-drawer__panel pf-m-width-33">
                            <slot name="panel"></slot>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
}
