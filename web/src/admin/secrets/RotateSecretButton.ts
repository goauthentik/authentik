import "#elements/SecretValue";
import "#elements/dialogs/ak-modal";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";
import { docLink } from "#common/global";
import { MessageLevel } from "#common/messages";

import { renderModal } from "#elements/dialogs/utils";
import { showAPIErrorMessage, showMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";

import { Secret, SecretsApi } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";

/**
 * An icon button that replaces a text secret with a generated value, after confirmation.
 * The confirmation opens in the top layer, so it also works inside a form modal.
 *
 * @param control Render as a bordered input-group control, for use next to an input.
 */
export function RotateSecretButton(secret: Secret, control = false): SlottedTemplateResult {
    const label = msg(str`Rotate ${secret.name}`, { id: "secret.rotate.label" });

    const confirm = async (event: Event, invoker: HTMLElement) => {
        const dialog = (event.currentTarget as HTMLElement).closest("dialog")!;
        const buttons = dialog.querySelectorAll<HTMLButtonElement>("button[slot=actions]");
        const closedBy = dialog.closedBy;

        buttons.forEach((button) => (button.disabled = true));
        dialog.closedBy = "none";

        try {
            const result = await aki(SecretsApi).secretsSecretsRotateCreate({
                secretUuid: secret.pk,
            });

            dialog.close();

            showMessage({
                message: msg("Successfully rotated secret.", { id: "secret.rotate.success" }),
                level: MessageLevel.success,
            });

            if (result.value) {
                await renderModal(
                    html`<ak-secret-value
                        label=${msg("New value", { id: "secret.rotate.result.label" })}
                        value=${result.value}
                    ></ak-secret-value>`,
                    {
                        headline: msg("Secret rotated", { id: "secret.rotate.result.header" }),
                        invokerElement: invoker,
                        size: PFSize.Medium,
                    },
                );
            }
        } catch (error) {
            await showAPIErrorMessage(error);
        } finally {
            buttons.forEach((button) => (button.disabled = false));
            dialog.closedBy = closedBy;
        }
    };

    const open = async (event: Event) => {
        // Read the invoker before any await: event targets inside a shadow tree are cleared once
        // dispatch finishes.
        const invoker = event.currentTarget as HTMLElement;

        const usedBy = await aki(SecretsApi)
            .secretsSecretsUsedByList({ secretUuid: secret.pk })
            .catch(() => []);

        const cookieSecret = usedBy.some((object) => object.modelName === "proxyprovider");

        return renderModal(
            html`<p>
                    ${msg(
                        "This replaces the value in authentik for every object using this secret.",
                        { id: "secret.rotate.confirm.description" },
                    )}
                </p>
                <p>
                    <strong
                        >${msg(
                            "This does not update external systems or software. Update them yourself to use the new value.",
                            { id: "secret.rotate.confirm.external-systems.description" },
                        )}</strong
                    >
                </p>
                ${
                    cookieSecret
                        ? html`<p>
                              ${msg(
                                  "Proxy providers sign their session cookies with this secret. Rotating it signs out every user of those providers.",
                                  { id: "secret.rotate.confirm.proxy-sessions.description" },
                              )}
                          </p>`
                        : nothing
                }
                ${
                    invoker.closest("form")
                        ? html`<p>
                              ${msg(
                                  "Rotating applies immediately, even if you don't save this form.",
                                  {
                                      id: "secret.rotate.confirm.unsaved.description",
                                  },
                              )}
                          </p>`
                        : nothing
                }
                <p>
                    <a
                        href=${docLink("/sys-mgmt/secrets/manage-secrets/#rotate-a-secret")}
                        target="_blank"
                        rel="noopener noreferrer"
                        >${msg("Learn about secret rotation", {
                            id: "secret.rotate.confirm.docs.label",
                        })}</a
                    >
                </p>
                <button
                    slot="actions"
                    type="button"
                    class="pf-c-button pf-m-link"
                    @click=${(event: Event) =>
                        (event.currentTarget as HTMLElement).closest("dialog")?.close()}
                >
                    ${msg("Cancel", { id: "common.actions.cancel.label" })}
                </button>
                <button
                    slot="actions"
                    type="button"
                    class="pf-c-button pf-m-danger"
                    @click=${(event: Event) => confirm(event, invoker)}
                >
                    ${msg("Rotate", { id: "secret.rotate.confirm.action" })}
                </button>`,
            {
                headline: msg("Rotate secret", { id: "secret.rotate.confirm.header" }),
                size: PFSize.Medium,
                invokerElement: invoker,
            },
        );
    };

    return html`<button
        class="pf-c-button ${control ? "pf-m-control" : "pf-m-plain"}"
        type="button"
        aria-label=${label}
        @click=${open}
    >
        <pf-tooltip position="top" content=${msg("Rotate secret", { id: "secret.rotate.tooltip" })}>
            <i class="fas fa-sync-alt" aria-hidden="true"></i>
        </pf-tooltip>
    </button>`;
}
