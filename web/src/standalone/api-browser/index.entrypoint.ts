import "rapidoc";
import "#types/rapi-doc";

import styles from "./index.entrypoint.css";

import { CSRFHeaderName } from "#common/api/middleware";
import { createUIThemeEffect } from "#common/theme";
import { getCookie } from "#common/utils";

import { Interface } from "#elements/Interface";
import { WithBrandConfig } from "#elements/mixins/branding";
import { ThemedImage } from "#elements/utils/images";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

export const BEFORE_TRY_EVENT = "before-try";

export interface BeforeTryEventDetail {
    request: {
        headers: Headers;
    };
}

function rgba2hex(cssValue: string) {
    const matches = /^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+\.{0,1}\d*))?\)$/.exec(cssValue);
    if (!matches) return "";

    return `#${matches
        .slice(1)
        .map((n, i) =>
            (i === 3 ? Math.round(parseFloat(n) * 255) : parseFloat(n))
                .toString(16)
                .padStart(2, "0")
                .replace("NaN", ""),
        )
        .join("")}`;
}

@customElement("ak-api-browser")
export class APIBrowser extends WithBrandConfig(Interface) {
    @property()
    schemaPath?: string;

    static styles: CSSResult[] = [styles];

    @state()
    bgColor = "#000000";

    @state()
    textColor = "#000000";

    #appendCSRFHeader = (event: CustomEvent<BeforeTryEventDetail>) => {
        event.detail.request.headers.append(CSRFHeaderName, getCookie("authentik_csrf"));
    };

    constructor() {
        super();
        this.addEventListener(BEFORE_TRY_EVENT, this.#appendCSRFHeader);
    }

    #synchronizeTheme = () => {
        const style = getComputedStyle(document.body);

        this.bgColor = rgba2hex(style.backgroundColor.trim());
        this.textColor = rgba2hex(style.color.trim());
    };

    public override connectedCallback(): void {
        super.connectedCallback();

        this.#synchronizeTheme();
        createUIThemeEffect(this.#synchronizeTheme);
    }

    render(): TemplateResult {
        return html`
            <rapi-doc
                part="rapi-doc"
                spec-url=${ifDefined(this.schemaPath)}
                heading-text=""
                theme="light"
                render-style="read"
                default-schema-tab="schema"
                primary-color="#fd4b2d"
                nav-bg-color="#212427"
                bg-color=${this.bgColor}
                text-color=${this.textColor}
                nav-text-color="#ffffff"
                nav-hover-bg-color="#3c3f42"
                nav-accent-color="#4f5255"
                nav-hover-text-color="#ffffff"
                use-path-in-nav-bar="true"
                nav-item-spacing="relaxed"
                allow-server-selection="false"
                show-header="false"
                allow-spec-url-load="false"
                allow-spec-file-load="false"
                show-method-in-nav-bar="as-colored-text"
            >
                <div slot="nav-logo">
                    ${ThemedImage({
                        src: this.brandingLogo,
                        alt: msg("authentik Logo"),
                        className: "logo",
                        theme: this.activeTheme,
                    })}
                </div>
            </rapi-doc>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-api-browser": APIBrowser;
    }
}

declare global {
    interface HTMLElementEventMap {
        [BEFORE_TRY_EVENT]: CustomEvent<BeforeTryEventDetail>;
    }
}
