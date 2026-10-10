import "#elements/forms/SearchSelect/index";
import HostStyles from "./ak-secret-search-input.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { renderModal } from "#elements/dialogs";
import { AKFormSubmittedEvent } from "#elements/forms/events";
import type { SearchSelect } from "#elements/forms/SearchSelect/ak-search-select";
import type { SearchSelectChangeEvent } from "#elements/forms/SearchSelect/events";
import { type SearchSelectSource, withQuery } from "#elements/forms/SearchSelect/shared";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { HorizontalLightComponent } from "#components/HorizontalLightComponent";

import { RotateSecretButton } from "#admin/secrets/RotateSecretButton";
import { SecretForm } from "#admin/secrets/SecretForm";
import { SecretValueButton } from "#admin/secrets/SecretValueButton";

import { Secret, SecretsApi, SecretTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

/**
 * Secret Search Input Component
 *
 * Search/select dropdown for Secret objects, with a button and pinned action to
 * create one on the fly without leaving the form. Mirrors `ak-file-search-input`.
 */
@customElement("ak-secret-search-input")
export class AKSecretSearchInput extends HorizontalLightComponent<string> {
    public static hostStyles = [PFButton, PFInputGroup, HostStyles];

    @property({ type: String })
    public override value = "";

    @property({ type: Boolean })
    public blankable = false;

    @property({ attribute: false })
    public types: SecretTypeEnum[] = [SecretTypeEnum.Text];

    protected secretSearchRef = createRef<SearchSelect<Secret>>();

    @state()
    protected selectedSecret: Secret | null = null;

    protected source: SearchSelectSource<Secret> = {
        fetchObjects: async (query) => {
            const { results } = await aki(SecretsApi).secretsSecretsList(
                withQuery(query, { ordering: "name", typeIn: this.types, pageSize: 100 }),
            );

            if (query || !this.value) return results;

            let selected = results.find((secret) => secret.pk === this.value);

            // The selected secret may sort beyond the first page, or the user may not be allowed
            // to view it. Keep it either way, so saving the form doesn't clear the reference.
            if (!selected) {
                selected = await aki(SecretsApi)
                    .secretsSecretsRetrieve({ secretUuid: this.value })
                    .catch(
                        () =>
                            ({
                                pk: this.value,
                                name: msg("Secret not visible", {
                                    id: "secret.picker.hidden.label",
                                }),
                            }) as Secret,
                    );

                results.unshift(selected);
            }

            this.selectedSecret = selected;

            return results;
        },
        keyOf: (secret) => secret.pk,
        labelOf: (secret) => secret.name,
    };

    protected openSecretCreateModal = (invocationEvent?: Event) => {
        invocationEvent?.stopPropagation();

        const secretForm = new SecretForm();
        secretForm.types = this.types;

        secretForm.addEventListener(AKFormSubmittedEvent.eventName, (event) => {
            const secret = (event as AKFormSubmittedEvent<Secret>).response;
            const secretSearch = this.secretSearchRef.value;

            this.value = secret.pk;
            this.selectedSecret = secret;

            if (secretSearch) {
                secretSearch.selectedObject = secret;
                secretSearch.value = secret.pk;

                return secretSearch.refresh();
            }
        });

        return renderModal(secretForm, {
            invokerElement:
                invocationEvent?.currentTarget instanceof HTMLElement
                    ? invocationEvent.currentTarget
                    : this,
            size: PFSize.Medium,
        });
    };

    protected changeListener = (event: SearchSelectChangeEvent<Secret>) => {
        this.value = event.detail.value?.pk ?? "";
        this.selectedSecret = event.detail.value;
    };

    protected override renderControl(): SlottedTemplateResult {
        const createLabel = msg("Create secret", { id: "secret.picker.create.label" });
        const secret = this.selectedSecret;

        // The picker updates itself after creating or rotating a secret. Letting the refresh
        // reach the surrounding form would reload it and discard unsaved changes.
        return html`<div
            class="pf-c-input-group"
            @ak-refresh=${(event: Event) => event.stopPropagation()}
        >
            <ak-search-select
                ${ref(this.secretSearchRef)}
                class="ak-secret-search-input__select"
                id=${ifPresent(this.fieldID)}
                name=${ifPresent(this.name)}
                .source=${this.source}
                .value=${this.value}
                placeholder=${msg("Select a secret...", { id: "secret.picker.value.placeholder" })}
                ?required=${this.required}
                ?blankable=${this.blankable}
                @ak-change=${this.changeListener}
                action-label=${createLabel}
                @ak-search-select-action=${this.openSecretCreateModal}
            ></ak-search-select>
            <button
                @click=${this.openSecretCreateModal}
                type="button"
                class="pf-c-button pf-m-control"
                aria-label=${createLabel}
                title=${createLabel}
            >
                <i class="fas fa-plus" aria-hidden="true"></i>
            </button>
            ${secret?.type ? SecretValueButton(secret, true) : nothing}
            ${secret?.type === SecretTypeEnum.Text ? RotateSecretButton(secret, true) : nothing}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-search-input": AKSecretSearchInput;
    }
}
