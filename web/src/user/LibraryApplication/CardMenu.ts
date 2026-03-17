import "#elements/AppIcon";
import "#user/LibraryApplication/RACLaunchEndpointModal";
import "#elements/buttons/Dropdown";

import { truncateWords } from "#common/strings";

import { LitFC } from "#elements/types";

import { Application } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import type { HTMLAttributes } from "react";

import { msg, str } from "@lit/localize";
import { html } from "lit";

export const AnchorPositionSupported = CSS.supports("position-anchor", "--test");

export interface CardMenuProps extends HTMLAttributes<HTMLDivElement> {
    cardID: string;
    descriptionID: string;
    application: Application;
    editURL?: string | URL | null;
}

export const CardMenu: LitFC<CardMenuProps> = ({
    application,
    cardID,
    descriptionID,
    editURL,
    ...props
}) => {
    const { metaDescription, metaPublisher } = application;
    const truncatedDescription = truncateWords(metaDescription, 50);

    const menuID = `${cardID}-actions-menu`;
    const menuAnchor = `--${cardID}-actions-menu-anchor`;

    if (!metaPublisher && !truncatedDescription && !editURL) {
        return null;
    }

    const applicationName = application.name || msg("application");

    return html`<div class="pf-c-dropdown" part="card-header-actions" ${spread(props)}>
        <button
            part="card-header-actions-button"
            class="pf-c-dropdown__toggle"
            type="button"
            style="anchor-name: ${menuAnchor};"
            popovertarget=${menuID}
            popovertargetaction="toggle"
            tabindex="-1"
            aria-label=${msg(str`Actions for "${applicationName}"`)}
        >
            <span part="card-header-actions-icon" class="pf-c-dropdown__toggle-text">&vellip;</span>
        </button>
        <menu
            class="pf-c-dropdown__menu"
            part="card-header-actions-menu"
            style="position-anchor: ${menuAnchor};"
            id=${menuID}
            ?popover=${AnchorPositionSupported}
        >
            ${metaPublisher || truncatedDescription
                ? html`<li role="presentation">
                          <div
                              part="card-header-action"
                              role="contentinfo"
                              class="pf-c-dropdown__menu-item"
                          >
                              ${metaPublisher
                                  ? html`<div part="card-header-action-publisher">
                                        <small>${metaPublisher}</small>
                                    </div>`
                                  : null}
                              ${truncatedDescription
                                  ? html`<p
                                        class="pf-c-content"
                                        part="card-header-action-description"
                                        id=${descriptionID}
                                    >
                                        ${truncatedDescription}
                                    </p>`
                                  : null}
                          </div>
                      </li>
                      <hr class="pf-c-divider" />`
                : null}
            ${editURL
                ? html`<li role="presentation">
                      <a
                          part="card-header-action"
                          role="menuitem"
                          href=${editURL.toString()}
                          class="pf-c-dropdown__menu-item"
                      >
                          <i class="fas fa-edit" role="img"></i>
                          &nbsp;${msg(str`Edit application...`)}</a
                      >
                  </li>`
                : null}
        </menu>
    </div>`;
};
