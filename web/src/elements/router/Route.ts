import { TemplateResult, html } from "lit";

export const SLUG_REGEX = "[-a-zA-Z0-9_]+";
export const ID_REGEX = "\\d+";
export const UUID_REGEX = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}";

export interface RouteArgs {
    [key: string]: string;
}

export class Route {
    url: RegExp;

    private element?: TemplateResult;
    private callback?: (args: RouteArgs) => TemplateResult;

    constructor(url: RegExp, element?: TemplateResult) {
        this.url = url;
        this.element = element;
    }

    redirect(to: string): Route {
        this.callback = () => {
            console.debug(`authentik/router: redirecting ${to}`);
            window.location.hash = `#${to}`;
            return html``;
        };
        return this;
    }

    redirectRaw(to: string): Route {
        this.callback = () => {
            console.debug(`authentik/router: redirecting ${to}`);
            window.location.hash = `${to}`;
            return html``;
        };
        return this;
    }

    then(render: (args: RouteArgs) => TemplateResult): Route {
        this.callback = render;
        return this;
    }

    render(args: RouteArgs): TemplateResult {
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
