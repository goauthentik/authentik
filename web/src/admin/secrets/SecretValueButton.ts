import "#elements/SecretValue";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import { aki } from "#common/api/client";
import { downloadFile } from "#common/download";
import { PFSize } from "#common/enums";

import { renderModal } from "#elements/dialogs";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";

import { Secret, SecretsApi, SecretTypeEnum } from "@goauthentik/api";

import { toByteArray } from "base64-js";

import { msg } from "@lit/localize";
import { html } from "lit";

export function SecretValueButton(secret: Secret, control = false) {
    const isFile = secret.type === SecretTypeEnum.File;

    const label = isFile
        ? msg("Download secret", { id: "secret.value.download.label" })
        : msg("View secret", { id: "secret.value.view.label" });

    const view = async (event: Event) => {
        const button = event.currentTarget as HTMLButtonElement;
        button.disabled = true;

        try {
            const { value } = await aki(SecretsApi).secretsSecretsViewValueRetrieve({
                secretUuid: secret.pk,
            });

            if (isFile) {
                downloadFile({
                    content: Uint8Array.from(toByteArray(value)).buffer,
                    filename: secret.name,
                });
            } else {
                button.disabled = false;
                button.focus();

                await renderModal(
                    html`<ak-secret-value
                        .value=${value}
                        .label=${msg("Value", { id: "secret.value.label" })}
                        ?multiline=${secret.type === SecretTypeEnum.Multiline}
                    ></ak-secret-value>`,
                    { headline: secret.name, invokerElement: button, size: PFSize.Medium },
                );
            }
        } catch (error) {
            await showAPIErrorMessage(error);
        } finally {
            button.disabled = false;
        }
    };

    return html`<button
        type="button"
        class="pf-c-button ${control ? "pf-m-control" : "pf-m-plain"}"
        aria-label=${label}
        @click=${view}
    >
        <pf-tooltip position="top" content=${label}>
            <i class=${isFile ? "fas fa-download" : "fas fa-eye"} aria-hidden="true"></i>
        </pf-tooltip>
    </button>`;
}
