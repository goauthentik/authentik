import { NavbarRenderProps } from "./ak-page-navbar.types";

import { UIConfig } from "#common/ui/config";

import { SessionUser } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";

function iconTemplate(iconIsImage: boolean, icon?: string) {
    if (icon) {
        if (iconIsImage && !icon.startsWith("fa://")) {
            return html`<img
                aria-hidden="true"
                class="accent-icon pf-icon"
                src="${icon}"
                alt="page icon"
            />`;
        }

        const fonticon = icon.replaceAll("fa://", "fa ");
        return html`<i class="accent-icon ${fonticon}" aria-hidden="true"></i>`;
    }
    return nothing;
}

const brandTemplate = (open: boolean, logo: string) =>
    html` <aside role="presentation" class="brand ${open ? "" : "pf-m-collapsed"}">
        <a aria-label="${msg("Home")}" href="#/">
            <div class="logo">
                <img src=${logo} alt="${msg("authentik Logo")}" loading="lazy" />
            </div>
        </a>
    </aside>`;

const navButtonTemplate = (open: boolean, onClick: () => void) =>
    html` <button
        aria-controls="global-nav"
        class="sidebar-trigger pf-c-button pf-m-plain"
        @click=${onClick}
        aria-label=${open ? msg("Collapse navigation") : msg("Expand navigation")}
        aria-expanded=${open ? "true" : "false"}
    >
        <i aria-hidden="true" class="fas fa-bars"></i>
    </button>`;

const contentHeaderTemplate = (
    title: string,
    iconIsImage: boolean,
    description?: string,
    icon?: string,
) =>
    html` <div class="items primary pf-c-content ${description ? "block-sibling" : ""}">
            <h1 aria-labelledby="page-navbar-heading" class="page-title">
                ${icon
                    ? html`<slot aria-hidden="true" name="icon"
                          >${iconTemplate(iconIsImage, icon)}</slot
                      >`
                    : nothing}
                <span id="page-navbar-heading">${title}</span>
            </h1>
        </div>
        ${description
            ? html`<div
                  role="heading"
                  aria-level="2"
                  aria-label="${description}"
                  class="items page-description pf-c-content"
              >
                  <p>${description}</p>
              </div>`
            : nothing}`;

const toolbarTemplate = (base: string, uiConfig?: UIConfig, session?: SessionUser) =>
    html` <div class="items secondary">
        <div class="pf-c-page__header-tools-group">
            <ak-nav-buttons .uiConfig=${uiConfig} .me=${session}>
                <a
                    class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none pf-u-display-block-on-md"
                    href="${base}if/user/"
                    slot="extra"
                >
                    ${msg("User interface")}
                </a>
            </ak-nav-buttons>
        </div>
    </div>`;

function navbarTemplate(props: NavbarRenderProps) {
    const { open, logo, onClick, title, base, uiConfig, session, description, icon, iconIsImage } =
        props;
    return html` <slot><!-- TODO: What is this for? --></slot>
        <div role="banner" aria-label="Main" class="main-content">
            ${brandTemplate(open, logo)}
            <!-- -->
            ${navButtonTemplate(open, onClick)}
            <!-- -->
            ${contentHeaderTemplate(title, iconIsImage, description, icon)}
            <!-- -->
            ${toolbarTemplate(base, uiConfig, session)}
        </div>`;
}

export default navbarTemplate;
