import "#elements/ak-array-input";
import "#components/ak-text-input";
import "#components/ak-switch-input";
import "#components/ak-number-input";
import "#elements/forms/FormGroup";
import "#elements/CodeMirror/ak-codemirror";

import { aki } from "#common/api/client";
import { groupBy } from "#common/utils";

import { ModelForm } from "#elements/forms/ModelForm";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { CoreApi, ModelEnum, ObjectAttribute, ObjectAttributeTypeEnum } from "@goauthentik/api";

import { match } from "ts-pattern";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { state } from "lit/decorators.js";

export interface ObjectAttributeOptions {
    disableRawAttributes: boolean;
}

export type AttributesMixin = {
    attributes?: Record<string, unknown>;
};

/**
 * Renders a single attribute based on its definition and the provided values.
 *
 * @param values the current values of the attributes.
 * @param def the definition of the attribute to render.
 */
function renderSingleAttribute(
    values: Record<string, unknown>,
    def: Pick<ObjectAttribute, "key" | "label" | "isRequired" | "type">,
): SlottedTemplateResult {
    const defaultValue = match(def.type)
        .with(ObjectAttributeTypeEnum.Text, () => "")
        .with(ObjectAttributeTypeEnum.Number, () => 0)
        .with(ObjectAttributeTypeEnum.Boolean, () => false)
        .otherwise(() => "");
    const value = values[def.key] || defaultValue;
    const name = def.key ? `attributes.${def.key}` : "";
    const { label, isRequired, type } = def;

    return match(type)
        .with(ObjectAttributeTypeEnum.Text, () => {
            return html`<ak-text-input
                name=${ifPresent(name)}
                label=${ifPresent(label)}
                autocomplete="off"
                .value=${value}
                ?required=${isRequired}
            ></ak-text-input>`;
        })
        .with(ObjectAttributeTypeEnum.Number, () => {
            return html`<ak-number-input
                name=${ifPresent(name)}
                label=${ifPresent(label)}
                .value=${value}
                ?required=${isRequired}
            ></ak-number-input>`;
        })
        .with(ObjectAttributeTypeEnum.Boolean, () => {
            return html`<ak-switch-input
                name=${ifPresent(name)}
                label=${ifPresent(label)}
                ?checked=${value}
                ?required=${isRequired}
            ></ak-switch-input>`;
        })
        .otherwise(() => {
            return html`<div>Unknown attribute type ${def.type} for ${def.key}</div>`;
        });
}

function renderArrayAttribute(
    values: Record<string, unknown>,
    def: ObjectAttribute,
): SlottedTemplateResult {
    const initialItems = values[def.key];
    const items: unknown[] = Array.isArray(initialItems) ? initialItems : [];

    return html`<ak-form-element-horizontal label=${def.label} name="attributes.${def.key}">
        <ak-array-input
            .items=${items}
            .newItem=${() => {
                return def.type === ObjectAttributeTypeEnum.Number ? 0 : "";
            }}
            .row=${(item: string, idx: number): SlottedTemplateResult => {
                const key = `${def.key}.${idx}`;
                const { isRequired, type } = def;

                return renderSingleAttribute({ [key]: item }, { key, isRequired, type, label: "" });
            }}
        ></ak-array-input>
    </ak-form-element-horizontal>`;
}

export abstract class ObjectAttributeModelForm<
    T extends object = object,
    PKT extends string | number = string | number,
    D = T,
> extends ModelForm<T, PKT, D> {
    @state()
    protected objAttributes: ObjectAttribute[] = [];

    public abstract model: ModelEnum;

    protected override async load() {
        const [app, model] = this.model.split(".");

        return aki(CoreApi)
            .coreObjectAttributesList({
                objectTypeAppLabel: app,
                objectTypeModel: model,
                enabled: true,
            })
            .then(({ results }) => {
                this.objAttributes = results;
            })
            .catch(showAPIErrorMessage);
    }

    protected renderObjectAttributes(
        defs: ObjectAttribute[],
        obj: AttributesMixin | null,
        options?: ObjectAttributeOptions,
    ): SlottedTemplateResult {
        const values = obj?.attributes || {};

        const renderAttributeValue = (groupedAttrDef: ObjectAttribute) => {
            if (groupedAttrDef.isArray) {
                return renderArrayAttribute(values, groupedAttrDef);
            }

            return renderSingleAttribute(values, groupedAttrDef);
        };

        return [
            groupBy(defs, (def) => def.group || "").map(([group, groupedAttrs]) => {
                if (!group) {
                    return groupedAttrs.map(renderAttributeValue);
                }

                return html`<ak-form-group label=${group} open>
                    <div class="pf-c-form">${groupedAttrs.map(renderAttributeValue)}</div>
                </ak-form-group>`;
            }),
            options?.disableRawAttributes
                ? null
                : html`<ak-form-group label=${msg("Advanced settings")}>
                      <div class="pf-c-form">
                          <ak-form-element-horizontal label=${msg("Attributes")} name="attributes">
                              <ak-codemirror mode="yaml" value="${YAML.stringify(values)}">
                              </ak-codemirror>
                              <p class="pf-c-form__helper-text">
                                  ${msg("Set custom attributes using YAML or JSON.")}
                              </p>
                          </ak-form-element-horizontal>
                      </div>
                  </ak-form-group>`,
        ];
    }
}
