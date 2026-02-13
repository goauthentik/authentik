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
import { html, nothing } from "lit";
import { classMap } from "lit/directives/class-map.js";
import { createRef, ref, RefOrCallback } from "lit/directives/ref.js";
import { styleMap } from "lit/directives/style-map.js";

const RAC_LAUNCH_URL = "goauthentik.io://providers/rac/launch";

export interface AKLibraryAppProps extends HTMLAttributes<HTMLDivElement> {
    application?: Application;
    editURL?: string | URL | null;
    background?: string | null;
    targetRef?: RefOrCallback | null;
}

export const AKLibraryApp: LitFC<AKLibraryAppProps> = ({
    application,
    editURL,
    background,
    className = "",
    targetRef,
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

    const cardID = `app-${application.pk}`;
    const titleID = `${cardID}-title`;
    const descriptionID = `${cardID}-description`;
    const cardHeader = CardHeader({
        application,
        id: titleID,
    });

    const rac = application.launchUrl === RAC_LAUNCH_URL;
    const primaryRef = targetRef ? ref(targetRef) : nothing;

    const extendedProps = {
        "aria-label": msg(str`Open "${application.name}"`, {
            id: "library.application.card.aria-label",
            desc: "Screen reader label for the application card",
        }),
        "tabindex": "0",
        "class": "card-header-aspect-wrapper",
        "title": ifPresent(application.name),
        "id": cardID,
        ...props,
    };

    return html`<div
        part="card-wrapper"
        data-application-name=${ifPresent(dataID)}
        style=${styleMap({ background: background || null })}
    >
        <div part="card" class="pf-c-card pf-m-hoverable pf-m-compact ${classMap(classes)}">
            <ak-app-icon
                exportparts="icon:card-header-icon"
                size=${PFSize.Large}
                name=${application.name}
                icon=${ifPresent(application.metaIconUrl)}
                .iconThemedUrls=${application.metaIconThemedUrls}
            ></ak-app-icon>
            ${rac
                ? html`<div
                      ${primaryRef}
                      role="button"
                      aria-describedby=${descriptionID}
                      @click=${launchModal}
                      ${spread(extendedProps)}
                  >
                      ${cardHeader}
                  </div>`
                : html`<a
                      ${primaryRef}
                      href=${ifPresent(application.launchUrl)}
                      target=${ifPresent(application.openInNewTab, "_blank")}
                      aria-describedby=${descriptionID}
                      ${spread(extendedProps)}
                      >${cardHeader}</a
                  >`}
            ${CardMenu({
                application,
                cardID,
                descriptionID,
                editURL,
            })}
        </div>
        ${rac
            ? html`<ak-library-rac-endpoint-launch
                  ${ref(modalRef)}
                  .app=${application}
              ></ak-library-rac-endpoint-launch>`
            : nothing}
    </div>`;
};
