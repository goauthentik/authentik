import { LitElement, html, customElement } from "lit-element";

@customElement("pb-tabs")
export class Tabs extends LitElement {
    _currentPage? = "";
    _firstPage? = "";

    get currentPage() {
        return this._currentPage;
    }

    set currentPage(value) {
        try {
            // Show active tab page
            this.querySelector(
                `.pf-c-tab-content[tab-name='${value}']`
            )?.removeAttribute("hidden");
            // Update active status on buttons
            this.querySelector(
                `.pf-c-tabs__item[tab-name='${value}']`
            )?.classList.add("pf-m-current");
            // Hide other tab pages
            this.querySelectorAll(
                `.pf-c-tab-content:not([tab-name='${value}'])`
            ).forEach((el) => {
                el.setAttribute("hidden", "");
            });
            // Update active status on other buttons
            this.querySelectorAll(
                `.pf-c-tabs__item:not([tab-name='${value}'])`
            ).forEach((el) => {
                el.classList.remove("pf-m-current");
            });
            // Update window hash
            window.location.hash = `#${value}`;
            this._currentPage = value;
        } catch (e) {
            this.currentPage = this._firstPage;
        }
    }

    createRenderRoot() {
        return this;
    }

    firstUpdated() {
        this._firstPage = this.querySelector(".pf-c-tab-content")?.getAttribute(
            "tab-name"
        )!;
        if (window.location.hash) {
            this.currentPage = window.location.hash;
        } else {
            this.currentPage = this._firstPage;
        }
        this.querySelectorAll(".pf-c-tabs__item > button").forEach((button) => {
            button.addEventListener("click", (e) => {
                let tabPage = button.parentElement?.getAttribute("tab-name")!;
                this.currentPage = tabPage;
            });
        });
    }
}
