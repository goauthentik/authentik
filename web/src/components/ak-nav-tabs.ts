import { AKElement } from "#elements/Base";
import { RouterNavigateEvent } from "#elements/router/core/navigation";

import { css } from "lit";
import { html } from "lit-html";
import { customElement, property, state } from "lit/decorators.js";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";

export interface NavItem {
    link: string;
    label: string;
}

@customElement("ak-nav-tabs")
export class NavTabs extends AKElement {
    public static readonly styles = [
        PFNav,
        css`
            .pf-c-nav.pf-m-horizontal {
                --pf-c-nav__link--m-current--Color: var(--ak-accent);
                --pf-c-nav__link--hover--Color: var(--ak-accent);
                --pf-c-nav__link--focus--Color: var(--ak-accent);
                --pf-c-nav__link--active--Color: var(--ak-accent);
                --pf-c-nav__link--before--BorderColor: var(--ak-accent);
            }
            .pf-c-nav__link {
                --pf-c-nav__link--Color: var(--pf-global--Color--100);
            }
        `,
    ];

    @property({ attribute: false })
    items: NavItem[] = [];

    @state()
    currentItem?: NavItem;

    public synchronize = (): void => {
        const activePath = window.location.pathname;

        this.currentItem = this.items.find((item) => item.link === activePath);
    };

    public override connectedCallback(): void {
        super.connectedCallback();

        window.addEventListener(RouterNavigateEvent.eventName, this.synchronize);
        window.addEventListener("popstate", this.synchronize);

        this.synchronize();
    }

    public override disconnectedCallback(): void {
        window.removeEventListener(RouterNavigateEvent.eventName, this.synchronize);
        window.removeEventListener("popstate", this.synchronize);

        super.disconnectedCallback();
    }

    render() {
        return html`<nav class="pf-c-nav pf-m-horizontal">
            <ul class="pf-c-nav__list">
                ${this.items.map((item) => {
                    return html`<li class="pf-c-nav__item">
                        <a
                            class="pf-c-nav__link ${item.link === this.currentItem?.link
                                ? "pf-m-current"
                                : ""}"
                            href=${item.link}
                            >${item.label}</a
                        >
                    </li>`;
                })}
            </ul>
        </nav>`;
    }
}
