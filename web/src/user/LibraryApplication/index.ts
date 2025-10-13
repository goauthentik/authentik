import "#elements/AppIcon";
import "#user/LibraryApplication/RACLaunchEndpointModal";

import { PFSize } from "#common/enums";

import { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { CardHeader } from "#user/LibraryApplication/CardHeader";
import { CardMenu } from "#user/LibraryApplication/CardMenu";
import { RACLaunchEndpointModal } from "#user/LibraryApplication/RACLaunchEndpointModal";

import { Application } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { kebabCase } from "change-case";
import type { HTMLAttributes } from "react";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { createRef, ref } from "lit/directives/ref.js";
import { styleMap } from "lit/directives/style-map.js";

const RAC_LAUNCH_URL = "goauthentik.io://providers/rac/launch";

export interface AKLibraryAppProps extends HTMLAttributes<HTMLDivElement> {
    application?: Application;
    background?: string | null;
    appIndex: number;
    groupIndex: number;
}

export const AKLibraryApp: LitFC<AKLibraryAppProps> = ({
    application,
    background,
    appIndex,
    groupIndex,
    className = "",
    ...props
}) => {
    if (!application) {
        return html`<ak-spinner></ak-spinner>`;
    }

    const classes = {
        [className]: className.length,
    };

    const dataID = kebabCase(application.name);

    const modalRef = createRef<RACLaunchEndpointModal>();

    const launchModal = () => {
        modalRef.value?.show();
    };

    const cardID = `app-card-${groupIndex}-${appIndex}`;
    const titleID = `${cardID}-title`;
    const descriptionID = `${cardID}-description`;
    const cardHeader = CardHeader({
        application,
        id: titleID,
    });

    const rac = application.launchUrl === RAC_LAUNCH_URL;

    return html`<div
        role="gridcell"
        part="app-card"
        data-application-name=${ifPresent(dataID)}
        aria-labelledby=${titleID}
        aria-describedby=${descriptionID}
        style=${styleMap({ background: background || null })}
        ${spread(props)}
    >
        <div part="card" class="pf-c-card pf-m-hoverable pf-m-compact ${classMap(classes)}">
            <ak-app-icon
                part="card-header-icon"
                size=${PFSize.Large}
                name=${application.name}
                icon=${ifPresent(application.metaIcon)}
            ></ak-app-icon>
            ${rac
                ? html`<div
                      role="button"
                      tabindex="0"
                      @click=${launchModal}
                      class="card-header-aspect-wrapper"
                      aria-label=${msg(str`Open "${application.name}"`)}
                      title=${ifPresent(application.name)}
                  >
                      <ak-library-rac-endpoint-launch
                          ${ref(modalRef)}
                          .app=${application}
                      ></ak-library-rac-endpoint-launch>
                      ${cardHeader}
                  </div>`
                : html`<a
                      tabindex="0"
                      class="card-header-aspect-wrapper"
                      aria-label=${msg(str`Open "${application.name}"`)}
                      title=${ifPresent(application.name)}
                      href=${ifPresent(application.launchUrl)}
                      target=${ifPresent(application.openInNewTab, "_blank")}
                      >${cardHeader}</a
                  >`}
            ${CardMenu({
                application,
                cardID,
                descriptionID,
            })}
        </div>
    </div>`;
};
