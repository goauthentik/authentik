import { css, customElement, html, LitElement, property } from "lit-element";
// @ts-ignore
import PageStyle from "@patternfly/patternfly/components/Page/page.css";
// @ts-ignore
import GlobalsStyle from "@patternfly/patternfly/base/patternfly-globals.css";

@customElement("pb-sidebar-brand")
export class SidebarBrand extends LitElement {
    @property()
    brandLogo?: string;

    @property()
    brandTitle?: string;

    static get styles() {
        return [
            GlobalsStyle,
            PageStyle,
            css`
                .pf-c-brand {
                    font-family: "DIN 1451 Std";
                    line-height: 60px;
                    font-size: 3rem;
                    color: var(--pf-c-nav__link--m-current--Color);
                    display: flex;
                    flex-direction: row;
                    justify-content: center;
                    width: 100%;
                    margin: 0 1rem;
                    margin-bottom: 1.5rem;
                }
                .pf-c-brand img {
                    max-height: 60px;
                    margin-right: 8px;
                }
            `,
        ];
    }

    render() {
        return html` <a href="#/" class="pf-c-page__header-brand-link">
            <div class="pf-c-brand pb-brand">
                <img
                    src="${this.brandLogo}"
                    alt="passbook icon"
                    loading="lazy"
                />
                ${this.brandTitle ? html`<span>${this.brandTitle}</span>` : ""}
            </div>
        </a>`;
    }
}
