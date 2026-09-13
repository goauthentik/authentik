import "#elements/AppIcon";
import "#user/LibraryApplication/RACLaunchEndpointModal";

import { PFSize } from "#common/enums";

import { modalInvoker } from "#elements/dialogs";
import { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { CardMenu } from "#user/LibraryApplication/CardMenu";
import { RACLaunchEndpointLaunch } from "#user/LibraryApplication/RACLaunchEndpointModal";

import { Application } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import { kebabCase } from "change-case";
import type { HTMLAttributes } from "react";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { ref, RefOrCallback } from "lit/directives/ref.js";

const RAC_LAUNCH_URL = "goauthentik.io://providers/rac/launch";

export interface LibraryAppRowProps extends HTMLAttributes<HTMLDivElement> {
    application?: Application;
    editURL?: string | URL | null;
    targetRef?: RefOrCallback | null;
}

/**
 * A single application rendered as a wide row for the library list view.
 *
 * Shows the full application name without truncation, plus secondary metadata
 * (description, publisher, slug, group) on the same row to support
 * search-by-substring use cases like "AWS account ID alongside account name".
 */
export const LibraryAppRow: LitFC<LibraryAppRowProps> = ({
    application,
    editURL,
    targetRef,
    ...props
}) => {
    if (!application) {
        return html`<ak-spinner></ak-spinner>`;
    }

    const dataID = kebabCase(application.name);
    const rowID = `app-row-${application.pk}`;
    const titleID = `${rowID}-title`;
    const metaID = `${rowID}-meta`;
    const descriptionID = `${rowID}-description`;

    const rac = application.launchUrl === RAC_LAUNCH_URL;
    const primaryRef = targetRef ? ref(targetRef) : nothing;

    const metaParts: string[] = [];
    if (application.metaDescription) metaParts.push(application.metaDescription);
    if (application.metaPublisher) metaParts.push(application.metaPublisher);
    if (application.slug) metaParts.push(application.slug);

    const linkProps = {
        "aria-label": msg(str`Open "${application.name}"`, {
            id: "library.application.row.aria-label",
            desc: "Screen reader label for the application list row",
        }),
        "aria-labelledby": `${titleID}${metaParts.length ? ` ${metaID}` : ""}`,
        "tabindex": "0",
        "class": "app-row-link",
        "part": "row-link",
        "id": rowID,
        ...props,
    };

    const inner = html`
        <ak-app-icon
            exportparts="icon:row-icon"
            part="row-icon-host"
            size=${PFSize.Medium}
            name=${application.name}
            icon=${ifPresent(application.metaIconUrl)}
            .iconThemedUrls=${application.metaIconThemedUrls}
        ></ak-app-icon>
        <div part="row-text" class="row-text">
            <div id=${titleID} part="row-title" class="row-title">${application.name}</div>
            ${metaParts.length
                ? html`<div id=${metaID} part="row-meta" class="row-meta">
                      ${metaParts.join(" · ")}
                  </div>`
                : nothing}
        </div>
    `;

    const launcher = rac
        ? html`<div
              ${primaryRef}
              role="button"
              ${modalInvoker(RACLaunchEndpointLaunch, { app: application })}
              ${spread(linkProps)}
          >
              ${inner}
          </div>`
        : html`<a
              ${primaryRef}
              href=${ifPresent(application.launchUrl)}
              target=${ifPresent(application.openInNewTab, "_blank")}
              ${spread(linkProps)}
              >${inner}</a
          >`;

    return html`<li
        part="row"
        class="app-row"
        data-application-name=${ifPresent(dataID)}
        role="presentation"
    >
        ${launcher}
        ${CardMenu({
            application,
            cardID: rowID,
            descriptionID,
            editURL,
        })}
    </li>`;
};
