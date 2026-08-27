import "#elements/CodeMirror/ak-codemirror";
import "#components/ak-text-input";

import { docLink } from "#common/global";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

interface PropertyMapping {
    name: string;
    expression?: string;
}

export abstract class BasePropertyMappingForm<T extends PropertyMapping> extends ModelForm<
    T,
    string
> {
    protected docLink: string | URL = "/add-secure-apps/providers/property-mappings/expression";

    public static override verboseName = msg("Property Mapping");
    public static override verboseNamePlural = msg("Property Mappings");

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated mapping.")
            : msg("Successfully created mapping.");
    }

    renderExtraFields(): SlottedTemplateResult {
        return nothing;
    }

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
                label=${msg("Mapping Name")}
                placeholder=${msg("Type a name for this mapping...")}
                autocomplete="off"
                required
                name="name"
                value="${ifDefined(this.instance?.name)}"
            >
            </ak-text-input>
            ${this.renderExtraFields()}
            <ak-form-element-horizontal label=${msg("Expression")} required name="expression">
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.expression)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Expression using Python.")}
                    <a target="_blank" rel="noopener noreferrer" href=${docLink(this.docLink)}>
                        ${msg("See documentation for a list of all variables.")}
                    </a>
                </p>
            </ak-form-element-horizontal>`;
    }
}
