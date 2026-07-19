import { ROUTE_SEPARATOR } from "#common/constants";

import { AKElement } from "#elements/Base";
import { listen } from "#elements/decorators/listen";

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

    @listen("hashchange", { target: window })
    public synchronize = (): void => {
        const activePath = window.location.hash.slice(1).split(ROUTE_SEPARATOR)[0];
        const currents = this.items.filter((item) => {
            const ourPath = item.link.split(";")[0];
            const pathIsWholePath = new RegExp(`^${ourPath}$`).test(activePath);
            return pathIsWholePath;
        });
        this.currentItem = currents.length > 0 ? currents[0] : undefined;
    };

    public override connectedCallback(): void {
        super.connectedCallback();
        this.synchronize();
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
                            href="#${item.link}"
                            >${item.label}</a
                        >
                    </li>`;
                })}
            </ul>
        </nav>`;
    }
}
