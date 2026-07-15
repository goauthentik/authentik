import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";
import "#components/ak-switch-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    AdminApi,
    AdminModelsListRequest,
    App,
    CoreApi,
    ObjectAttribute,
    ObjectAttributeTypeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-object-attribute-form")
export class ObjectAttributeForm extends ModelForm<ObjectAttribute, string> {
    async loadInstance(pk: string): Promise<ObjectAttribute> {
        return aki(CoreApi).coreObjectAttributesRetrieve({
            attributeId: pk,
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated attribute.")
            : msg("Successfully created attribute.");
    }

    async send(data: ObjectAttribute): Promise<ObjectAttribute> {
        if (data.regex === "") {
            data.regex = undefined;
        }

        if (this.instance?.pk) {
            return aki(CoreApi).coreObjectAttributesUpdate({
                attributeId: this.instance.pk,
                objectAttributeRequest: data,
            });
        }

        return aki(CoreApi).coreObjectAttributesCreate({
            objectAttributeRequest: data,
        });
    }

    //#region Renders

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                name="label"
                value="${this.instance?.label ?? ""}"
                label=${msg("Label")}
                placeholder=${msg("Type a human-readable name...")}
                required
                help=${msg("Human-readable name of this attribute.")}
            ></ak-text-input>
            <ak-text-input
                name="key"
                value="${this.instance?.key ?? ""}"
                label=${msg("Key")}
                placeholder=${msg("Type a unique identifier...")}
                required
                help=${msg(
                    "Unique identifier per object type, which is used as a key in the attributes field.",
                )}
            ></ak-text-input>
            <ak-text-input
                name="group"
                value="${this.instance?.group ?? ""}"
                label=${msg("Group")}
                placeholder=${msg("Type an optional group identifier...")}
                help=${msg("Optional grouping for this attribute in forms.")}
            ></ak-text-input>
            <ak-switch-input
                name="enabled"
                label=${msg("Enabled")}
                ?checked=${this.instance?.enabled ?? true}
                help=${msg(
                    "When checked, attribute will be shown in forms for the selected object type.",
                )}
            ></ak-switch-input>
            <ak-form-element-horizontal label=${msg("Type")} required name="type">
                <ak-radio
                    .options=${[
                        {
                            label: msg("Text"),
                            value: ObjectAttributeTypeEnum.Text,
                            default: true,
                        },
                        {
                            label: msg("Number"),
                            value: ObjectAttributeTypeEnum.Number,
                        },
                        {
                            label: msg("Boolean"),
                            value: ObjectAttributeTypeEnum.Boolean,
                        },
                    ]}
                    .value=${this.instance?.type}
                >
                </ak-radio>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Object type")} name="objectType" required>
                <ak-search-select
                    .fetchObjects=${(): Promise<App[]> => {
                        const args: AdminModelsListRequest = {
                            filterHasAttributes: true,
                        };

                        return aki(AdminApi).adminModelsList(args);
                    }}
                    .renderElement=${(app: App): string => app.label}
                    .value=${(app?: App) => app?.name}
                    .selected=${(app: App): boolean => {
                        return app.name === this.instance?.objectTypeObj.fullyQualifiedModel;
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>

            <ak-form-group label=${msg("Validation")} open>
                <div class="pf-c-form">
                    <ak-switch-input
                        name="isRequired"
                        label=${msg("Attribute is required")}
                        ?checked=${this.instance?.isRequired}
                        help=${msg("Value of the attribute cannot be empty.")}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="isUnique"
                        label=${msg("Attribute is unique")}
                        ?checked=${this.instance?.isUnique}
                        help=${msg(
                            "Value of the attribute must be unique across all instances of the selected object type.",
                        )}
                    ></ak-switch-input>
                    <ak-switch-input
                        name="isArray"
                        label=${msg("Attribute is an array")}
                        ?checked=${this.instance?.isArray}
                        help=${msg("Value can have multiple entries.")}
                    ></ak-switch-input>
                    <ak-text-input
                        name="regex"
                        value="${this.instance?.regex ?? ""}"
                        label=${msg("RegEx")}
                        input-hint="code"
                        placeholder=${msg("Enter an optional Regular Expression for validation...")}
                        help=${msg(
                            "Optional RegEx to validate any value against. Uses the Python RegEx engine.",
                        )}
                    ></ak-text-input>
                </div>
            </ak-form-group>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-object-attribute-form": ObjectAttributeForm;
    }
}
