import { DualSelectPair } from "#elements/ak-dual-select/types";

import { WebAuthnDeviceType } from "@goauthentik/api";

import { html } from "lit";

export function deviceTypeRestrictionPair(item: WebAuthnDeviceType): DualSelectPair {
    const label = item.description ? item.description : item.aaguid;
    return [
        item.aaguid,
        html`<div class="selection-main">${label}</div>
            <div class="selection-desc">${item.aaguid}</div>`,
        label,
    ];
}
