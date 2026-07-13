import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    CoreApi,
    CoreUsersListRequest,
    PamApi,
    PamPersonaTemplatesListRequest,
    Persona,
    PersonaCreateRequest,
    PersonaTemplate,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-persona-form")
export class PersonaForm extends ModelForm<Persona, number, Partial<PersonaCreateRequest>> {
    public static override verboseName = msg("Persona");
    public static override verboseNamePlural = msg("Personas");

    async loadInstance(pk: number): Promise<Persona> {
        return aki(PamApi).pamPersonasRetrieve({ id: pk });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated persona.")
            : msg("Successfully created persona.");
    }

    protected override async send(data: Partial<PersonaCreateRequest>): Promise<Persona> {
        if (this.instance) {
            return aki(PamApi).pamPersonasPartialUpdate({
                id: this.instance.pk,
                patchedPersonaRequest: data,
            });
        }
        return aki(PamApi).pamPersonasCreate({
            personaCreateRequest: data as PersonaCreateRequest,
        });
    }

    protected renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                label=${msg("Name")}
                name="name"
                required
                value="${this.instance?.name ?? ""}"
                placeholder=${msg("Type a name for this persona...")}
            ></ak-text-input>
            ${this.instance
                ? html``
                : html`<ak-form-element-horizontal label=${msg("User")} required name="asUser">
                      <ak-search-select
                          placeholder=${msg("Select a user...")}
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
                          .renderElement=${(user: User): string => {
                              return user.username;
                          }}
                          .renderDescription=${(user: User): TemplateResult => {
                              return html`${user.name}`;
                          }}
                          .value=${(user: User | undefined): number | undefined => {
                              return user?.pk;
                          }}
                      >
                      </ak-search-select>
                  </ak-form-element-horizontal>`}
            <ak-form-element-horizontal label=${msg("Template")} name="template">
                <ak-search-select
                    placeholder=${msg("None (no delegation to agents)")}
                    blankable
                    .fetchObjects=${async (query?: string): Promise<PersonaTemplate[]> => {
                        const args: PamPersonaTemplatesListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const templates = await aki(PamApi).pamPersonaTemplatesList(args);
                        return templates.results;
                    }}
                    .renderElement=${(template: PersonaTemplate): string => {
                        return template.name;
                    }}
                    .value=${(template: PersonaTemplate | undefined): string | undefined => {
                        return template?.uuid;
                    }}
                    .selected=${(template: PersonaTemplate): boolean => {
                        return this.instance?.template === template.uuid;
                    }}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Determines which actors (agents) may present an actor_token to obtain a token exchanged for this persona. See Persona Templates.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-persona-form": PersonaForm;
    }
}
