import "#elements/CodeMirror/ak-codemirror";
import "#components/ak-text-input";

import { docLink } from "#common/global";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { property } from "lit/decorators.js";
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

    @property({ type: Boolean })
    public copyMode = false;

    getSuccessMessage(): string {
        return this.instancePk
            ? msg("Successfully updated mapping.")
            : msg("Successfully created mapping.");
    }

    protected override assignInstance(instance: T | null): void {
        if (instance && this.copyMode) {
            this.instancePk = null;
            super.assignInstance({ ...instance, name: `${instance.name} - copy` });
            return;
        }
        super.assignInstance(instance);
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
