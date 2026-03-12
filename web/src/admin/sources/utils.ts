import { FontAwesomeProtocol, parseFontAwesomeIcon } from "#elements/utils/images";

import { PolicyBindingCheckTarget } from "#admin/policies/utils";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";

export function renderSourceIcon(name: string, iconUrl: string | undefined | null): TemplateResult {
    const icon = html`<i
        part="source-icon"
        role="img"
        class="fas fa-share-square"
        title="${name}"
    ></i>`;
    if (iconUrl) {
        if (iconUrl.startsWith(FontAwesomeProtocol)) {
            const { family, iconClass } = parseFontAwesomeIcon(iconUrl);
            return html`<i
                part="source-icon"
                role="img"
                class="${family} ${iconClass}"
                title="${name}"
            ></i>`;
        }
        return html`<img part="source-icon" src="${iconUrl}" alt="${name}" />`;
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
