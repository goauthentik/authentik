import { aki } from "#common/api/client";
import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { PamApi, Persona } from "@goauthentik/api";

import { html } from "lit-html";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-persona-form")
export class PersonaForm extends ModelForm<Persona> {
    protected async send(data: Persona): Promise<unknown> {
        return aki(PamApi).pamPersonasCreate({
            personaCreateRequest: {
                name: data.name,
            }
        })
    }

    protected renderForm(): SlottedTemplateResult | null {
        return html``;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-persona-form": PersonaForm;
    }
}
