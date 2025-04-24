/**
 * @file Sidebar utilities.
 *
 * @todo This needs a revision to better align with Docusaurus's components.
 */

const html = String.raw;

/**
 *
 * @param {string[]} releases
 * @returns
 */
export function generateVersionDropdown(releases) {
    return html`<div
            class="navbar__item dropdown dropdown--hoverable dropdown--right psuedo-dropdown"
        >
            <style>
                .psuedo-dropdown .navbar__link.menu__link {
                    display: flex;
                    width: 100%;
                    justify-content: space-between;
                    font-weight: var(--ifm-font-weight-semibold);
                }
                .psuedo-dropdown .navbar__link.menu__link::after {
                    color: var(--ifm-color-emphasis-400);
                    filter: var(--ifm-menu-link-sublist-icon-filter);
                    margin-inline-end: calc(var(--ifm-navbar-padding-horizontal) * 0.5);
                }

                .psuedo-dropdown .dropdown__menu {
                    background: var(--ifm-dropdown-background-color);
                    box-shadow: var(--ifm-global-shadow-lw);
                    border: 1px solid var(--ifm-color-emphasis-200);
                }
            </style>

            <div
                aria-haspopup="true"
                aria-expanded="false"
                role="button"
                class="navbar__link menu__link"
            >
                Version: Pre-Release
            </div>

            <ul class="dropdown__menu menu__list-item--collapsed">
                ${releases
                    .map((release, idx) => {
                        const version = release.replace(/releases\/\d+\/v/, "");
                        const subdomain = `version-${version.replace(".", "-")}`;
                        const label = `Version: ${version}${idx === 0 ? " (Current)" : ""}`;

                        return html`<li>
                            <a
                                href="https://${subdomain}.goauthentik.io/docs"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="dropdown__link menu__link"
                                >${label}</a
                            >
                        </li>`;
                    })
                    .join("")}
            </ul>
        </div>
        <hr />`;
}
