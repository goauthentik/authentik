import { html, TemplateResult } from "lit-html";

export const SLUG_REGEX = "[-a-zA-Z0-9_]+";

export class Route {
    url: RegExp;

    private element?: TemplateResult;
    private callback?: (args: { [key: string]: string }) => TemplateResult;

    constructor(url: RegExp, element?: TemplateResult) {
        this.url = url;
        this.element = element;
    }

    redirect(to: string): Route {
        this.callback = () => {
            console.debug(`passbook/router: redirecting ${to}`);
            window.location.hash = `#${to}`;
            return html``;
        };
        return this;
    }

    then(render: (args: { [key: string]: string }) => TemplateResult): Route {
        this.callback = render;
        return this;
    }

    render(args: { [key: string]: string }): TemplateResult {
        if (this.callback) {
            return this.callback(args);
        }
        if (this.element) {
            return this.element;
        }
        throw new Error("Route does not have callback or element");
    }

    toString(): string {
        return `<Route url=${this.url} callback=${this.callback ? "true" : "false"}>`;
    }
}
