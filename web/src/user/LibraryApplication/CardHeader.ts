import { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { Application } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";
import type { HTMLAttributes } from "react";

import { html } from "lit";

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
    application: Application;
}

export const CardHeader: LitFC<CardHeaderProps> = ({ application, ...props }) => {
    return html`<div
        part="card-header"
        class="pf-c-card__header pf-m-pressable"
        aria-label=${ifPresent(application.name)}
        title=${ifPresent(application.name)}
        ${spread(props)}
    >
        <div id="app-title" class="pf-c-card__title pf-m-pressable" part="card-title">
            <div class="clamp-wrapper">${application.name}</div>
        </div>
    </div>`;
};
