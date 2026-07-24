import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";
import "#components/ak-switch-input";

import { aki } from "#common/api/client";
import { dateTimeLocal } from "#common/temporal";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import {
    CoreApi,
    CoreUsersListRequest,
    Persona,
    PersonaCreateRequest,
    PersonasApi,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-persona-form")
export class PersonaForm extends Form<PersonaCreateRequest> {
    public static override verboseName = msg("Persona");
    public static override verboseNamePlural = msg("Personas");
    public static override createLabel = msg("Create");
    public static override submitVerb = msg("Create");

    @state()
    protected expiresAt: Date | null = null;

    getSuccessMessage(): string {
        return msg("Successfully created persona.");
    }

    async send(data: PersonaCreateRequest): Promise<Persona> {
        return aki(PersonasApi).personasPersonasCreate({
            personaCreateRequest: data,
        });
    }

    #expiringChangeListener = (event: Event) => {
        const expiringElement = event.target as HTMLInputElement;
        this.expiresAt = expiringElement.checked ? new Date() : null;
    };

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Parent user")} name="parent" required>
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await aki(CoreApi).coreUsersList(args);
                        return users.results;
                    }}
                    .renderElement=${(user: User) => user.username}
                    .renderDescription=${(user: User) => html`${user.name}`}
                    .value=${(user: User | null) => user?.pk}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg("The user this persona acts on behalf of.")}
                </p>
            </ak-form-element-horizontal>

            <ak-text-input
                name="label"
                label=${msg("Label")}
                value=""
                help=${msg("Optional display name. Defaults to the parent user's name.")}
            ></ak-text-input>

            <ak-switch-input
                name="expiring"
                label=${msg("Expiring")}
                help=${msg("Whether this persona should be automatically removed once it expires.")}
                @change=${this.#expiringChangeListener}
                ?checked=${!!this.expiresAt}
            ></ak-switch-input>

            <ak-form-element-horizontal name="expires">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "persona-expiration-date-input",
                    },
                    msg("Expires on"),
                )}

                <input
                    id="persona-expiration-date-input"
                    type="datetime-local"
                    data-type="datetime-local"
                    value=${this.expiresAt ? dateTimeLocal(this.expiresAt) : ""}
                    ?disabled=${!this.expiresAt}
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-persona-form": PersonaForm;
    }
}
