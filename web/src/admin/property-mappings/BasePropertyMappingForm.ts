import "#elements/CodeMirror/ak-codemirror";
import "#components/ak-radio-input";
import "#components/ak-text-input";
import { docLink } from "#common/global";

import { ModelForm } from "#elements/forms/ModelForm";
import { RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";

import { ListMergeModeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

interface PropertyMapping {
    name: string;
    expression?: string;
    listMergeMode?: ListMergeModeEnum;
}

const listMergeModeOptions: RadioOption<ListMergeModeEnum>[] = [
    {
        label: msg("Append"),
        value: ListMergeModeEnum.Append,
        description: html`${msg("Add every item to the existing list.")}`,
    },
    {
        label: msg("Append unique items"),
        value: ListMergeModeEnum.AppendUnique,
        description: html`${msg("Add only the items that are not already in the list.")}`,
    },
    {
        label: msg("Replace"),
        value: ListMergeModeEnum.Replace,
        description: html`${msg("Replace the existing list.")}`,
    },
];

export abstract class BasePropertyMappingForm<T extends PropertyMapping> extends ModelForm<
    T,
    string
> {
    protected docLink: string | URL = "/add-secure-apps/providers/property-mappings/expression";

    /**
     * Default list merge mode of this mapping type. Only set for mapping types whose
     * results are merged with the results of other mappings.
     */
    protected listMergeModeDefault: ListMergeModeEnum | null = null;

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

    protected renderListMergeMode(): SlottedTemplateResult {
        if (!this.listMergeModeDefault) {
            return nothing;
        }

        return html`<ak-radio-input
            name="listMergeMode"
            label=${msg("List merging")}
            .value=${this.instance?.listMergeMode ?? this.listMergeModeDefault}
            .options=${listMergeModeOptions}
            .help=${msg(
                "How lists that this mapping returns are combined with lists already present under the same key, such as lists from mappings evaluated before it.",
            )}
        >
        </ak-radio-input>`;
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
            </ak-form-element-horizontal>
            ${this.renderListMergeMode()}`;
    }
}
