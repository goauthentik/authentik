import { docLink } from "@goauthentik/common/global.js";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

interface PropertyMapping {
    name: string;
    expression?: string;
}

export abstract class BasePropertyMappingForm<T extends PropertyMapping> extends ModelForm<
    T,
    string
> {
    docLink(): string {
        return "/docs/add-secure-apps/providers/property-mappings/expression?utm_source=authentik";
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated mapping.")
            : msg("Successfully created mapping.");
    }

    renderExtraFields(): TemplateResult {
        return html``;
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            ${this.renderExtraFields()}
            <ak-form-element-horizontal label=${msg("Expression")} required name="expression">
                <ak-codemirror
                    mode=${CodeMirrorMode.Python}
                    value="${ifDefined(this.instance?.expression)}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Expression using Python.")}
                    <a target="_blank" rel="noopener noreferrer" href="${docLink(this.docLink())}">
                        ${msg("See documentation for a list of all variables.")}
                    </a>
                </p>
            </ak-form-element-horizontal>`;
    }
}
