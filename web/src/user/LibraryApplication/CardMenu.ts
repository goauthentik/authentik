import "#elements/AppIcon";
import "#user/LibraryApplication/RACLaunchEndpointModal";
import "#elements/buttons/Dropdown";

import { globalAK } from "#common/global";
import { truncateWords } from "#common/strings";
import { rootInterface } from "#common/theme";

import { LitFC } from "#elements/types";

import type { UserInterface } from "#user/index.entrypoint";

import { Application } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import type { HTMLAttributes } from "react";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";

export interface CardMenuProps extends HTMLAttributes<HTMLDivElement> {
    cardID: string;
    descriptionID: string;
    application: Application;
}

export const CardMenu: LitFC<CardMenuProps> = ({
    application,
    cardID,
    descriptionID,
    ...props
}) => {
    const { me, uiConfig } = rootInterface<UserInterface>();

    const editURL =
        uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser
            ? `${globalAK().api.base}if/admin/#/core/applications/${application.slug}`
            : null;

    const { metaDescription, metaPublisher } = application;
    const truncatedDescription = truncateWords(metaDescription, 50);

    const menuID = `${cardID}-actions-menu`;
    const menuAnchor = `--${cardID}-actions-menu-anchor`;

    return html`<div class="pf-c-dropdown" part="card-header-actions" ${spread(props)}>
        <button
            part="card-header-actions-button"
            class="pf-c-dropdown__toggle"
            type="button"
            id="add-mfa-toggle"
            style="anchor-name: ${menuAnchor};"
            aria-haspopup="menu"
            aria-controls=${menuID}
            popovertarget=${menuID}
            popovertargetaction="toggle"
            tabindex="-1"
            aria-label=${msg(str`Actions for "${application.name}"`)}
        >
            <span part="card-header-actions-icon" class="pf-c-dropdown__toggle-text">&vellip;</span>
        </button>
        <menu
            class="pf-c-dropdown__menu"
            part="card-header-actions-menu"
            style="position-anchor: ${menuAnchor};"
            id=${menuID}
            popover
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
                                  : nothing}
                              ${metaPublisher
                                  ? html`<p
                                        class="pf-c-content"
                                        part="card-header-action-description"
                                        id=${descriptionID}
                                    >
                                        ${truncatedDescription}
                                    </p>`
                                  : nothing}
                          </div>
                      </li>
                      <hr class="pf-c-divider" />`
                : nothing}
            ${editURL
                ? html`<li role="presentation">
                      <a
                          part="card-header-action"
                          role="menuitem"
                          href=${editURL}
                          class="pf-c-dropdown__menu-item"
                      >
                          <i class="fas fa-edit" aria-hidden="true"></i>
                          &nbsp;${msg(str`Edit application...`)}</a
                      >
                  </li>`
                : nothing}
        </menu>
    </div>`;
};
