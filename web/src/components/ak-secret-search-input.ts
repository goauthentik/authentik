import "#elements/forms/SearchSelect/index";

import HostStyles from "./ak-secret-search-input.css";

import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";

import { IconRotateSecretButton } from "#elements/buttons/IconRotateSecretButton";
import { renderModal } from "#elements/dialogs";
import { AKFormSubmittedEvent } from "#elements/forms/events";
import SearchSelect from "#elements/forms/SearchSelect/index";
import { SlottedTemplateResult } from "#elements/types";

import { HorizontalLightComponent } from "#components/HorizontalLightComponent";

import { SecretForm } from "#admin/secrets/SecretForm";
import { SecretValueButton } from "#admin/secrets/SecretValueButton";

import { Secret, SecretsApi, SecretTypeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { createRef, ref } from "lit/directives/ref.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

const renderElement = (item: Secret) => item.name;
const renderValue = (item?: Secret | null) => item?.pk;

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

    protected secretSearchRef = createRef<SearchSelect>();

    @state()
    protected selectedSecret?: Secret;

    protected openSecretCreateModal = (invocationEvent?: Event) => {
        invocationEvent?.stopPropagation();

        const secretForm = new SecretForm();

        secretForm.addEventListener(AKFormSubmittedEvent.eventName, (event) => {
            this.value = (event as AKFormSubmittedEvent<Secret>).response.pk;
            const secretSearch = this.secretSearchRef.value;
            if (secretSearch) {
                secretSearch.query = undefined;
                return secretSearch.updateData();
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

    #selected = (item: Secret) => {
        return this.value === item.pk;
    };

    protected changeListener = (event: CustomEvent<{ value: Secret | null }>) => {
        this.value = event.detail.value?.pk ?? "";
        this.selectedSecret = event.detail.value ?? undefined;
    };

    protected refresh = async (query?: string): Promise<Secret[]> => {
        const secrets = await aki(SecretsApi).secretsSecretsList({
            ordering: "name",
            pageSize: 100,
            ...(query ? { search: query } : {}),
        });

        // The selected secret may sort beyond the first page; make sure it is present so
        // the control can display and keep it instead of silently clearing on save.
        if (!query && this.value && !secrets.results.some((secret) => secret.pk === this.value)) {
            const selected = await aki(SecretsApi).secretsSecretsRetrieve({
                secretUuid: this.value,
            });
            return [selected, ...secrets.results];
        }

        return secrets.results;
    };

    protected override renderControl(): SlottedTemplateResult {
        const createLabel = msg("Create secret", { id: "secret-picker.create-action.label" });

        return html`<div class="pf-c-input-group">
            <ak-search-select
                ${ref(this.secretSearchRef)}
                class="ak-secret-search-input__select"
                .fieldID=${this.fieldID}
                .label=${this.label ?? undefined}
                .fetchObjects=${this.refresh}
                .renderElement=${renderElement}
                .value=${renderValue}
                .selected=${this.#selected}
                placeholder=${msg("Select a secret...", {
                    id: "secret-picker.value.placeholder",
                })}
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
            ${this.selectedSecret ? SecretValueButton(this.selectedSecret, true) : nothing}
            ${this.value && this.selectedSecret?.type === SecretTypeEnum.Text
                ? IconRotateSecretButton({
                      control: true,
                      rotate: () =>
                          aki(SecretsApi).secretsSecretsRotateCreate({
                              secretUuid: this.value,
                          }),
                  })
                : nothing}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-secret-search-input": AKSecretSearchInput;
    }
}
