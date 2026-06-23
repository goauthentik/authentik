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

function renderSingleAttribute(attrs: Record<string, unknown>, attr: ObjectAttribute) {
    return match(attr.type)
        .with(ObjectAttributeTypeEnum.Text, () => {
            return html`<ak-text-input
                name="attributes.${attr.key}"
                label=${attr.label}
                autocomplete="off"
                .value="${attrs[attr.key]}"
                ?required=${attr.isRequired}
            ></ak-text-input>`;
        })
        .with(ObjectAttributeTypeEnum.Number, () => {
            return html`<ak-number-input
                name="attributes.${attr.key}"
                label=${attr.label}
                .value="${attrs[attr.key]}"
                ?required=${attr.isRequired}
            ></ak-number-input>`;
        })
        .with(ObjectAttributeTypeEnum.Boolean, () => {
            return html`<ak-switch-input
                name="attributes.${attr.key}"
                label=${attr.label}
                ?checked=${attrs[attr.key]}
                ?required=${attr.isRequired}
            >
            </ak-switch-input>`;
        });
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
        const attributes = obj?.attributes || {};

        return [
            groupBy(defs, (def) => def.group || "").map(([group, groupedAttrs]) => {
                if (group === "") {
                    return groupedAttrs.map((attr) => renderSingleAttribute(attributes, attr));
                }
                return html`<ak-form-group label=${group}>
                    <div class="pf-c-form">
                        ${groupedAttrs.map((attr) => renderSingleAttribute(attributes, attr))}
                    </div>
                </ak-form-group>`;
            }),
            options?.disableRawAttributes
                ? null
                : html`<ak-form-group label=${msg("Advanced settings")}>
                      <div class="pf-c-form">
                          <ak-form-element-horizontal label=${msg("Attributes")} name="attributes">
                              <ak-codemirror mode="yaml" value="${YAML.stringify(attributes)}">
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
