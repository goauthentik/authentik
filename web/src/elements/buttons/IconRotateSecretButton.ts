import "#components/ak-hidden-text-input";
import "#elements/dialogs/ak-modal";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { AKRefreshEvent } from "#common/events";
import { MessageLevel } from "#common/messages";

import { renderConfirmation, renderModal } from "#elements/dialogs/utils";
import { showAPIErrorMessage, showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import { RotatedSecret } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";

export interface RotateSecretProps {
    /** Calls the rotate endpoint. */
    rotate: () => Promise<RotatedSecret>;
    /** Render as a bordered input-group control, for use next to an input. */
    control?: boolean;
}

/**
 * An icon button that replaces a secret with a newly generated one, after confirmation. The
 * confirmation opens in the top layer, so it also works inside a form modal.
 */
export function IconRotateSecretButton({
    rotate,
    control = false,
}: RotateSecretProps): SlottedTemplateResult {
    const headline = msg("Rotate secret", { id: "secret-rotate.confirm.header" });

    const open = async (event: Event) => {
        // Read the invoker before any await: event targets inside a shadow tree are cleared once
        // dispatch finishes.
        const invoker = event.currentTarget as HTMLElement;

        let secret: string | null | undefined;

        const confirmed = await renderConfirmation(
            html`<p>
                    ${msg(
                        "The old value stops working immediately. Update any external systems that use it.",
                        { id: "secret-rotate.confirm.warning" },
                    )}
                </p>
                ${invoker.closest("form")
                    ? html`<p>
                          ${msg("Rotating applies immediately, even if you don't save this form.", {
                              id: "secret-rotate.confirm.unsaved",
                          })}
                      </p>`
                    : nothing}`,
            async () => {
                try {
                    secret = (await rotate()).value;
                } catch (error) {
                    await showAPIErrorMessage(error);

                    throw error;
                }
            },
            {
                headline,
                action: msg("Rotate", { id: "secret-rotate.confirm.action" }),
                invokerElement: invoker,
            },
        );

        if (!confirmed) return;

        if (secret) {
            await renderModal(
                html`<ak-hidden-text-input
                    label=${msg("New secret", { id: "secret-rotate.result.label" })}
                    value=${secret}
                    readonly
                    revealed
                    copyable
                    input-hint="code"
                ></ak-hidden-text-input>`,
                {
                    headline: msg("Secret rotated", { id: "secret-rotate.result.header" }),
                    invokerElement: invoker,
                },
            );
        }

        invoker.dispatchEvent(new AKRefreshEvent());

        showMessage({
            message: msg("Successfully rotated secret.", { id: "secret-rotate.success" }),
            level: MessageLevel.success,
        });
    };

    return html`<button
        class="pf-c-button ${control ? "pf-m-control" : "pf-m-plain"}"
        type="button"
        aria-label=${headline}
        @click=${open}
    >
        <pf-tooltip position="top" content=${headline}>
            <i class="fas fa-sync-alt" aria-hidden="true"></i>
        </pf-tooltip>
    </button>`;
}
