import "#components/ak-text-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    oauth2ProvidersProvider,
    oauth2ProvidersSelector,
} from "#admin/providers/oauth2/OAuth2ProvidersProvider";
import {
    oauth2SourcesProvider,
    oauth2SourcesSelector,
} from "#admin/providers/oauth2/OAuth2Sources";

import { PamApi, PersonaTemplate } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement } from "lit/decorators.js";

@customElement("ak-persona-template-form")
export class PersonaTemplateForm extends ModelForm<PersonaTemplate, string> {
    public static override verboseName = msg("Persona Template");
    public static override verboseNamePlural = msg("Persona Templates");

    async loadInstance(pk: string): Promise<PersonaTemplate> {
        return aki(PamApi).pamPersonaTemplatesRetrieve({ uuid: pk });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated persona template.")
            : msg("Successfully created persona template.");
    }

    protected override async send(data: PersonaTemplate): Promise<PersonaTemplate> {
        if (this.instance) {
            return aki(PamApi).pamPersonaTemplatesUpdate({
                uuid: this.instance.uuid!,
                personaTemplateRequest: data,
            });
        }
        return aki(PamApi).pamPersonaTemplatesCreate({
            personaTemplateRequest: data,
        });
    }

    protected renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                label=${msg("Name")}
                name="name"
                required
                value="${ifDefined(this.instance?.name)}"
                placeholder=${msg("Type a name for this persona template...")}
            ></ak-text-input>
            <ak-form-element-horizontal label=${msg("Actor providers")} name="actorProviders">
                <ak-dual-select-dynamic-selected
                    .provider=${oauth2ProvidersProvider}
                    .selector=${oauth2ProvidersSelector(this.instance?.actorProviders)}
                    available-label=${msg("Available Providers")}
                    selected-label=${msg("Selected Providers")}
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "OAuth2/OIDC providers whose tokens may be presented as an actor_token to obtain a token exchanged for a persona instantiated from this template.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Actor sources")} name="actorSources">
                <ak-dual-select-dynamic-selected
                    .provider=${oauth2SourcesProvider}
                    .selector=${oauth2SourcesSelector(this.instance?.actorSources)}
                    available-label=${msg("Available Sources")}
                    selected-label=${msg("Selected Sources")}
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "OAuth sources whose tokens may be presented as an actor_token to obtain a token exchanged for a persona instantiated from this template.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-persona-template-form": PersonaTemplateForm;
    }
}
