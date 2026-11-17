import { PolicyBindingCheckTarget } from "#common/policies/utils";
import { resolveThemedUrl, ResolvedUITheme } from "#common/theme";

import type { ThemedUrls } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";

/**
 * Render a source icon, using the variant for the active theme when the icon has one.
 */
export function renderSourceIcon(
    name: string,
    iconUrl: string | undefined | null,
    iconThemedUrls: ThemedUrls | undefined | null,
    theme: ResolvedUITheme,
): TemplateResult {
    const icon = html`<i
        part="source-icon"
        role="img"
        class="fas fa-share-square"
        title="${name}"
    ></i>`;

    const resolvedUrl = resolveThemedUrl(theme, iconThemedUrls, iconUrl);

    if (resolvedUrl) {
        if (resolvedUrl.startsWith("fa://")) {
            const url = resolvedUrl.replaceAll("fa://", "");

            return html`<i part="source-icon" role="img" class="fas ${url}" title="${name}"></i>`;
        }

        return html`<img part="source-icon" src="${resolvedUrl}" alt="${name}" />`;
    }

    return icon;
}

export function sourceBindingTypeNotices() {
    return [
        {
            type: PolicyBindingCheckTarget.Group,
            notice: msg(
                "Group mappings can only be checked if a user is already logged in when trying to access this source.",
            ),
        },
        {
            type: PolicyBindingCheckTarget.User,
            notice: msg(
                "User mappings can only be checked if a user is already logged in when trying to access this source.",
            ),
        },
    ];
}
