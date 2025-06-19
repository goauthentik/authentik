import { PolicyBindingCheckTarget } from "@goauthentik/admin/policies/utils";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";

export function renderSourceIcon(name: string, iconUrl: string | undefined | null): TemplateResult {
    const icon = html`<i class="fas fa-share-square" title="${name}"></i>`;
    if (iconUrl) {
        if (iconUrl.startsWith("fa://")) {
            const url = iconUrl.replaceAll("fa://", "");
            return html`<i class="fas ${url}" title="${name}"></i>`;
        }
        return html`<img src="${iconUrl}" alt="${name}" />`;
    }
    return icon;
}

export function sourceBindingTypeNotices() {
    return [
        {
            type: PolicyBindingCheckTarget.group,
            notice: msg(
                "Group mappings can only be checked if a user is already logged in when trying to access this source.",
            ),
        },
        {
            type: PolicyBindingCheckTarget.user,
            notice: msg(
                "User mappings can only be checked if a user is already logged in when trying to access this source.",
            ),
        },
    ];
}

/**
 * Create a form submit handler for source forms that bubbles up the event
 *
 * This is used in specific source view pages to bubble up the form submission event
 * to the parent SourceViewPage component.
 *
 * @returns A function that can be used as an event handler for ak-form-successful-submit events
 */
export function createSourceFormSubmitHandler() {
    return (e: CustomEvent) => {
        const event = new CustomEvent("ak-form-successful-submit", {
            bubbles: true,
            composed: true,
            detail: e.detail,
        });
        e.currentTarget?.dispatchEvent(event);
    };
}
