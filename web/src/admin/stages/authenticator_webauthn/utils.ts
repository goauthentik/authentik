import "#components/ak-text-input";
import "#elements/ak-array-input";
import "#elements/forms/HorizontalFormElement";
import { DualSelectPair } from "#elements/ak-dual-select/types";

import { WebAuthnDeviceType } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";

export function additionalAcceptedOriginsField(name: string, origins: string[] = []) {
    return html`<ak-form-element-horizontal
        label=${msg("Additional accepted origins", { id: "webauthn.additional-origins.label" })}
        name=${name}
    >
        <ak-array-input
            .items=${origins}
            .newItem=${() => ""}
            .row=${(origin: string) => html`
                <ak-text-input
                    name="origin"
                    label=${msg("Origin", { id: "webauthn.additional-origins.entry.label" })}
                    .value=${origin}
                    input-hint="code"
                    required
                    style="width: 100%"
                ></ak-text-input>
            `}
        ></ak-array-input>
        <p class="pf-c-form__helper-text">
            ${msg(
                "Additional trusted HTTPS or android:apk-key-hash origins, matched exactly. The current request origin is always accepted. Android apps also require externally hosted Digital Asset Links on the relying-party domain.",
                { id: "webauthn.additional-origins.description" },
            )}
        </p>
    </ak-form-element-horizontal>`;
}

export function deviceTypeRestrictionPair(item: WebAuthnDeviceType): DualSelectPair {
    const label = item.description ? item.description : item.aaguid;

    return [
        item.aaguid,
        html`<div class="selection-main">${label}</div>
            <div class="selection-desc">${item.aaguid}</div>`,
        label,
    ];
}
