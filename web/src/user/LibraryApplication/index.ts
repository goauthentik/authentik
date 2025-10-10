import "#elements/AppIcon";
import "#elements/Expand";
import "#user/LibraryApplication/RACLaunchEndpointModal";

import { PFSize } from "#common/enums";
import { globalAK } from "#common/global";
import { truncateWords } from "#common/strings";
import { rootInterface } from "#common/theme";

import { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import type { UserInterface } from "#user/index.entrypoint";
import { RACLaunchEndpointModal } from "#user/LibraryApplication/RACLaunchEndpointModal";

import { Application } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { kebabCase } from "change-case";
import type { HTMLAttributes } from "react";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { createRef, ref } from "lit/directives/ref.js";
import { styleMap } from "lit/directives/style-map.js";

const RAC_LAUNCH_URL = "goauthentik.io://providers/rac/launch";

interface CardHeaderProps {
    application: Application;
}

const CardHeader: LitFC<CardHeaderProps> = ({ application }) => {
    return html`<div
        part="card-header"
        class="pf-c-card__header pf-m-pressable"
        aria-label=${msg(str`Open "${application.name}"`)}
        title=${ifPresent(application.name)}
        href=${ifPresent(application.launchUrl)}
        target=${ifPresent(application.openInNewTab, "_blank")}
    >
        <ak-app-icon
            part="card-header-icon"
            size=${PFSize.Large}
            name=${application.name}
            icon=${ifPresent(application.metaIcon)}
        ></ak-app-icon>
        <div id="app-title" class="pf-c-card__title pf-m-pressable" part="card-title">
            <div class="clamp-wrapper">${"Acme Corp VPN"}</div>
        </div>
    </div>`;
};

interface CardDetailsProps extends Pick<Application, "name" | "metaDescription" | "metaPublisher"> {
    editURL?: string | null;
}

const CardDetails: LitFC<CardDetailsProps> = ({
    metaPublisher,
    metaDescription,
    name,
    editURL,
}) => {
    const truncatedDescription = truncateWords(metaDescription, 10);
    const expansionLabel = msg("Details");

    return html`<ak-expand
        class="app-details"
        text-open=${expansionLabel}
        text-closed=${expansionLabel}
        >${metaPublisher || truncatedDescription
            ? html`<div class="pf-c-content" part="card-expansion">
                      <small>${metaPublisher}</small>
                  </div>
                  <div id="app-description" part="card-description">${truncatedDescription}</div>`
            : nothing}
        ${editURL
            ? html`
                  <a
                      slot="actions"
                      class="pf-c-button pf-m-link pf-m-small pf-m-block"
                      aria-label=${msg(str`Edit "${name}"`)}
                      href=${editURL}
                  >
                      <i class="fas fa-edit" aria-hidden="true"></i>&nbsp;${msg("Edit")}
                  </a>
              `
            : nothing}</ak-expand
    >`;
};

export interface AKLibraryAppProps extends HTMLAttributes<HTMLDivElement> {
    application?: Application;
    selected?: boolean;
    background?: string | null;
}

let counter = 0;

export const AKLibraryApp: LitFC<AKLibraryAppProps> = ({
    application,
    selected = false,
    background,
    className = "",
    ...props
}) => {
    if (!application) {
        return html`<ak-spinner></ak-spinner>`;
    }

    const { name, metaDescription, metaPublisher } = application;

    const classes = {
        [className]: className.length,
        "pf-m-selectable": selected,
        "pf-m-selected": selected,
    };

    const dataID = kebabCase(application.name);

    const { me, uiConfig } = rootInterface<UserInterface>();

    const editURL =
        uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser
            ? `${globalAK().api.base}if/admin/#/core/applications/${application?.slug}`
            : null;

    counter += 1;
    const modalRef = createRef<RACLaunchEndpointModal>();
    const launchModal = () => {
        modalRef.value?.show();
    };

    const cardHeader = CardHeader({
        application,
    });

    const rac = application.launchUrl === RAC_LAUNCH_URL;

    return html`<div
        role="gridcell"
        part="app-card"
        data-application-name=${ifPresent(dataID)}
        aria-labelledby="app-title"
        aria-describedby="app-description"
        style=${styleMap({ background: background || null })}
        ${spread(props)}
    >
        <div part="card" class="pf-c-card pf-m-hoverable pf-m-compact ${classMap(classes)}">
                ${
                    rac
                        ? html`<div
                              role="button"
                              tabindex="0"
                              @click=${launchModal}
                              class="card-header-aspect-wrapper"
                              aria-label=${msg(str`Open "${application.name}"`)}
                              title=${ifPresent(application.name)}
                          >
                              ${cardHeader}
                              <ak-library-rac-endpoint-launch
                                  ${ref(modalRef)}
                                  .app=${application}
                              ></ak-library-rac-endpoint-launch>
                          </div>`
                        : html`<a
                              class="card-header-aspect-wrapper"
                              aria-label=${msg(str`Open "${application.name}"`)}
                              title=${ifPresent(application.name)}
                              href=${ifPresent(application.launchUrl)}
                              target=${ifPresent(application.openInNewTab, "_blank")}
                              >${cardHeader}</a
                          >`
                }
            </div>
            ${CardDetails({
                name,
                metaDescription,
                metaPublisher,
                editURL,
            })}
        </div>
    </div>`;
};
