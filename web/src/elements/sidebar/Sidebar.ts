import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
// @ts-ignore
import PageStyle from "@patternfly/patternfly/components/Page/page.css";
// @ts-ignore
import NavStyle from "@patternfly/patternfly/components/Nav/nav.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";

import { until } from "lit-html/directives/until";

import "./SidebarBrand";
import "./SidebarUser";

export interface SidebarItem {
    name: string;
    path?: string[];
    children?: SidebarItem[];
    condition?: () => Promise<boolean>;
}

@customElement("ak-sidebar")
export class Sidebar extends LitElement {
    @property({attribute: false})
    items: SidebarItem[] = [];

    @property()
    activePath: string;

    static get styles(): CSSResult[] {
        return [
            GlobalsStyle,
            PageStyle,
            NavStyle,
            css`
                .pf-c-nav__list .sidebar-brand {
                    max-height: 82px;
                    margin-bottom: -0.5rem;
                }
                .pf-c-nav__link {
                    --pf-c-nav__link--PaddingTop: 0.5rem;
                    --pf-c-nav__link--PaddingRight: 0.5rem;
                    --pf-c-nav__link--PaddingBottom: 0.5rem;
                }
                .pf-c-nav__subnav {
                    --pf-c-nav__subnav--PaddingBottom: 0px;
                }

                .pf-c-nav__item-bottom {
                    position: absolute;
                    bottom: 0;
                    width: 100%;
                }
            `,
        ];
    }

    constructor() {
        super();
        this.activePath = window.location.hash.slice(1, Infinity);
        window.addEventListener("hashchange", () => {
            this.activePath = window.location.hash.slice(1, Infinity);
        });
    }

    async renderItem(item: SidebarItem): Promise<TemplateResult> {
        if (item.condition) {
            const result = await item.condition();
            if (!result) {
                return html``;
            }
        }
        return html` <li class="pf-c-nav__item ${item.children ? "pf-m-expandable pf-m-expanded" : ""}">
            ${item.path ?
        html`<a href="#${item.path}" class="pf-c-nav__link ${item.path.some((v) => v === this.activePath) ? "pf-m-current": ""}">
                        ${item.name}
                    </a>` :
        html`<a class="pf-c-nav__link" aria-expanded="true">
                        ${item.name}
                        <span class="pf-c-nav__toggle">
                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                        </span>
                    </a>
                    <section class="pf-c-nav__subnav">
                        <ul class="pf-c-nav__simple-list">
                            ${item.children?.map((i) => until(this.renderItem(i), html``))}
                        </ul>
                    </section>`}
        </li>`;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-page__sidebar-body">
            <nav class="pf-c-nav" aria-label="Global">
                <ul class="pf-c-nav__list">
                    <li class="pf-c-nav__item sidebar-brand">
                        <ak-sidebar-brand></ak-sidebar-brand>
                    </li>
                    ${this.items.map((i) => until(this.renderItem(i), html``))}
                    <li class="pf-c-nav__item pf-c-nav__item-bottom">
                        <ak-sidebar-user></ak-sidebar-user>
                    </li>
                </ul>
            </nav>
        </div>`;
    }
}
