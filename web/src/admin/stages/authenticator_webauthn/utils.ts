import { DualSelectPair } from "@goauthentik/elements/ak-dual-select/types";

import { html } from "lit";

import { WebAuthnDeviceType } from "@goauthentik/api";

export function deviceTypeRestrictionPair(item: WebAuthnDeviceType): DualSelectPair {
    const label = item.description ? item.description : item.aaguid;
    return [
        item.aaguid,
        html`<div class="selection-main">${label}</div>
            <div class="selection-desc">${item.aaguid}</div>`,
        label,
    ];
}
