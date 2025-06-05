import "#elements/sidebar/SidebarVersion";

import { AKElement } from "#elements/Base";

import { UiThemeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement } from "lit/decorators.js";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-sidebar")
export class Sidebar extends AKElement {
    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFNav,
            css`
                :host {
                    z-index: 100;
                    --pf-c-page__sidebar--Transition: 0 !important;
                }
                .pf-c-nav__link.pf-m-current::after,
                .pf-c-nav__link.pf-m-current:hover::after,
                .pf-c-nav__item.pf-m-current:not(.pf-m-expanded) .pf-c-nav__link::after {
                    --pf-c-nav__link--m-current--after--BorderColor: #fd4b2d;
                }
                :host([theme="light"]) {
                    border-right-color: transparent !important;
                }

                .pf-c-nav__section + .pf-c-nav__section {
                    --pf-c-nav__section--section--MarginTop: var(--pf-global--spacer--sm);
                }

                nav {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    overflow-y: hidden;
                }
                .pf-c-nav__list {
                    flex-grow: 1;
                    overflow-y: auto;
                }

                .pf-c-nav__link {
                    --pf-c-nav__link--PaddingTop: 0.5rem;
                    --pf-c-nav__link--PaddingRight: 0.5rem;
                    --pf-c-nav__link--PaddingBottom: 0.5rem;
                }
                .pf-c-nav__section-title {
                    font-size: 12px;
                }
                .pf-c-nav__item {
                    --pf-c-nav__item--MarginTop: 0px;
                }
            `,
        ];
    }

    render(): TemplateResult {
        return html`<nav
            class="pf-c-nav ${this.activeTheme === UiThemeEnum.Light ? "pf-m-light" : ""}"
            aria-label=${msg("Global")}
        >
            <ul class="pf-c-nav__list">
                <slot></slot>
            </ul>
            <ak-sidebar-version></ak-sidebar-version>
        </nav>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar": Sidebar;
    }
}
