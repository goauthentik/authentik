import { SlottedTemplateResult } from "#elements/types";

import { GrantRequest, RequestedApplication, RequestStatus } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit-html";

/**
 * A request's status as its requester and admins see it. An approved application request has
 * created an application, rather than granted access that lasts until it expires.
 */
export function requestStatusLabel({ status, requestedApplication }: GrantRequest): string {
    switch (status) {
        case RequestStatus.Approved:
            return requestedApplication
                ? msg("Created", { id: "requests.status.application-created" })
                : msg("Active");
        case RequestStatus.Denied:
            return msg("Denied");
        case RequestStatus.Revoked:
            return msg("Revoked");
        default:
            return msg("Pending");
    }
}

/**
 * Renders what a request is for: the new application an application request asks for, or else
 * the first of its targets (an Application or Application Entitlement, paired with its owning
 * Application), plus an overflow count for the rest.
 */
export function renderRequestSummary({
    targetObjs: targets = [],
    requestedApplication,
}: GrantRequest): SlottedTemplateResult {
    if (requestedApplication) {
        return msg(str`New application: ${requestedApplication.name}`, {
            id: "requests.summary.new-application",
        });
    }

    if (targets.length < 1) {
        return nothing;
    }

    const target = targets[0];
    const overflow = targets.length - 1;
    const label = target.parent ? `${target.parent?.name} / ${target.label}` : target.label;

    return html`${label} ${overflow > 0 ? `+${overflow}` : ""}`;
}

/**
 * Renders what an application request asks for, so reviewers see exactly what approving creates.
 * Requires PatternFly's description list styles in the host.
 */
export function renderRequestedApplication(app: RequestedApplication): SlottedTemplateResult {
    const rows: [string, SlottedTemplateResult][] = [
        [msg("Name", { id: "requests.requested-application.name.label" }), app.name],
        [
            msg("Client type", { id: "requests.requested-application.client-type.label" }),
            app.clientType,
        ],
        [
            msg("Grant types", { id: "requests.requested-application.grant-types.label" }),
            app.grantTypes.join(", "),
        ],
        [
            msg("Redirect URIs", { id: "requests.requested-application.redirect-uris.label" }),
            (app.redirectUris ?? []).length
                ? html`${(app.redirectUris ?? []).map((uri) => html`<div><code>${uri}</code></div>`)}`
                : msg("-"),
        ],
        [
            msg("Groups given access", { id: "requests.requested-application.groups.label" }),
            app.groupsObj.map((group) => group.name).join(", "),
        ],
        [
            msg("Launch URL", { id: "requests.requested-application.launch-url.label" }),
            app.metaLaunchUrl || msg("-"),
        ],
        [
            msg("Description", { id: "requests.requested-application.description.label" }),
            app.metaDescription || msg("-"),
        ],
    ];

    return html`<dl class="pf-c-description-list pf-m-horizontal">
        ${rows.map(
            ([term, description]) =>
                html`<div class="pf-c-description-list__group">
                    <dt class="pf-c-description-list__term">
                        <span class="pf-c-description-list__text">${term}</span>
                    </dt>
                    <dd class="pf-c-description-list__description">
                        <div class="pf-c-description-list__text">${description}</div>
                    </dd>
                </div>`,
        )}
    </dl>`;
}
