// sort-imports-ignore
/**
 * @file API Browser Entry Point.
 */

import "rapidoc";

import { CSRFHeaderName } from "@goauthentik/common/api/middleware";
import { createColorSchemeEffect } from "@goauthentik/common/color-scheme";
import { first, getCookie } from "@goauthentik/common/utils";
import { InterfaceElement } from "@goauthentik/elements/Interface";
import "@goauthentik/elements/ak-locale-context";
import { DefaultBrand } from "@goauthentik/elements/sidebar/SidebarBrand";
import { themeImage } from "@goauthentik/elements/utils/images";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-api-browser")
export class APIBrowser extends InterfaceElement {
    @property()
    schemaPath?: string;

    static get styles(): CSSResult[] {
        return [
            css`
                img.logo {
                    width: 100%;
                    padding: 1rem 0.5rem 1.5rem 0.5rem;
                    min-height: 48px;
                }
            `,
        ];
    }

    @state()
    bgColor = "#000000";

    @state()
    textColor = "#000000";

    readonly #colorSchemeAbortController = new AbortController();

    public firstUpdated(): void {
        createColorSchemeEffect(
            {
                colorScheme: "dark",
                signal: this.#colorSchemeAbortController.signal,
            },
            (matches) => {
                const style = getComputedStyle(document.documentElement);

                if (matches) {
                    this.bgColor = style.getPropertyValue("--ak-dark-background").trim();
                    this.textColor = style.getPropertyValue("--ak-dark-foreground").trim();
                } else {
                    this.bgColor = style
                        .getPropertyValue("--pf-global--BackgroundColor--light-300")
                        .trim();
                    this.textColor = style.getPropertyValue("--pf-global--Color--300").trim();
                }
            },
        );
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#colorSchemeAbortController.abort();
    }

    render(): TemplateResult {
        return html`
            <ak-locale-context>
                <rapi-doc
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
                    @before-try=${(
                        e: CustomEvent<{
                            request: {
                                headers: Headers;
                            };
                        }>,
                    ) => {
                        e.detail.request.headers.append(
                            CSRFHeaderName,
                            getCookie("authentik_csrf"),
                        );
                    }}
                >
                    <div slot="nav-logo">
                        <img
                            alt="${msg("authentik Logo")}"
                            class="logo"
                            src="${themeImage(
                                first(this.brand?.brandingLogo, DefaultBrand.brandingLogo),
                            )}"
                        />
                    </div>
                </rapi-doc>
            </ak-locale-context>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-api-browser": APIBrowser;
    }
}
