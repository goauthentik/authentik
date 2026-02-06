import { PolicyBindingCheckTarget } from "#admin/policies/utils";
import { ResolvedUITheme } from "#common/theme";

import { ThemedUrls } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";

function resolveSourceIconUrl(
    iconUrl: string | undefined | null,
    iconThemedUrls: ThemedUrls | undefined | null,
    theme: ResolvedUITheme | undefined,
): string | undefined | null {
    if (theme && iconThemedUrls?.[theme]) {
        return iconThemedUrls[theme];
    }
    return iconUrl;
}

export function renderSourceIcon(
    name: string,
    iconUrl: string | undefined | null,
    iconThemedUrls?: ThemedUrls | null,
    theme?: ResolvedUITheme,
): TemplateResult {
    const resolvedIconUrl = resolveSourceIconUrl(iconUrl, iconThemedUrls, theme);
    const icon = html`<i
        part="source-icon"
        role="img"
        class="fas fa-share-square"
        title="${name}"
    ></i>`;
    if (resolvedIconUrl) {
        if (resolvedIconUrl.startsWith("fa://")) {
            const url = resolvedIconUrl.replaceAll("fa://", "");
            return html`<i part="source-icon" role="img" class="fas ${url}" title="${name}"></i>`;
        }
        return html`<img part="source-icon" src="${resolvedIconUrl}" alt="${name}" />`;
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
