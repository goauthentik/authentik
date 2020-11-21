import { customElement, html, LitElement, property } from "lit-element";

interface RegexAnchor {
    anchor: HTMLAnchorElement;
    match: RegExp;
}

@customElement("pb-admin-sidebar")
export class AdminSideBar extends LitElement {
    @property()
    activePath: string;

    paths: RegexAnchor[] = [];

    constructor() {
        super();
        this.activePath = window.location.hash.slice(1, Infinity);
        window.addEventListener("hashchange", (e) => {
            this.activePath = window.location.hash.slice(1, Infinity);
        });
        this.querySelectorAll<HTMLAnchorElement>(".pf-c-nav__link").forEach(
            (a) => {
                let rawValue = a.attributes.getNamedItem("pb-url-prefix")
                    ?.value;
                if (!rawValue) {
                    const parsedURL = new URL(a.href);
                    if (parsedURL.hash === "") {
                        console.log(`Ignoring ${a}`);
                        return;
                    }
                    rawValue = `^${parsedURL.hash.slice(1, Infinity)}`;
                }
                const regexp = RegExp(rawValue);
                this.paths.push({ anchor: a, match: regexp });
            }
        );
    }

    render() {
        this.paths.forEach((path) => {
            if (path.match.exec(this.activePath)) {
                path.anchor.classList.add("pf-m-current");
            } else {
                path.anchor.classList.remove("pf-m-current");
            }
        });
        return html`<slot></slot>`;
    }
}
