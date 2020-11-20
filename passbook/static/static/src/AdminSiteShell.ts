import { customElement, html, LitElement, property } from "lit-element";

@customElement("pb-admin-shell")
export class AdminSiteShell extends LitElement {

    @property()
    set defaultUrl(value: string) {
        if (window.location.hash === "" && value !== undefined) {
            window.location.hash = `#${value}`;
        }
    }

    createRenderRoot() {
        return this;
    }

    constructor() {
        super();
        this.loadContent();
        window.addEventListener("hashchange", (e) => this.loadContent());
    }

    loadContent() {
        let url = window.location.hash.slice(1, Infinity);
        if (url === "") {
            return
        }
        fetch(url).then(r => r.text()).then((t) => {
            this.innerHTML = t;
        }).then(() => {
            this.querySelectorAll("a").forEach(a => {
                if (a.href === "") {
                    return;
                }
                try {
                    const url = new URL(a.href);
                    const qs = url.search || "";
                    a.href = `#${url.pathname}${qs}`;
                } catch (e) {
                    a.href = `#${a.href}`;
                }
            });
        });
    }

    render() {
        return html`${this.innerHTML}`;
    }

}
