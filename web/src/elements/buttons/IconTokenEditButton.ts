import { IconEditButton } from "#elements/dialogs/components/IconEditButton";
import { SlottedTemplateResult } from "#elements/types";

import { TokenForm } from "#admin/tokens/TokenForm";

import { Token } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { guard } from "lit-html/directives/guard.js";

function stopEventPropagation(event: Event): void {
    event.stopPropagation();
}

export function IconTokenEditButton(token?: Token | null): SlottedTemplateResult {
    return guard([token, token?.identifier, token?.managed], () => {
        if (!token) {
            return null;
        }

        if (token.managed) {
            const label = msg("Managed tokens cannot be edited.");
            return html`<pf-tooltip position="top" content=${label} @click=${stopEventPropagation}
                ><button type="button" class="pf-c-button pf-m-plain" disabled aria-label=${label}>
                    <i aria-hidden="true" class="fas fa-edit"></i>
                </button>
            </pf-tooltip>`;
        }

        return IconEditButton(TokenForm, token.identifier, token.identifier);
    });
}
