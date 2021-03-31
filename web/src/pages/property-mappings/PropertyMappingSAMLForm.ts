import { SAMLPropertyMapping, PropertymappingsApi } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";

@customElement("ak-property-mapping-saml-form")
export class PropertyMappingLDAPForm extends Form<SAMLPropertyMapping> {

    set mappingUUID(value: string) {
        new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlRead({
            pmUuid: value,
        }).then(mapping => {
            this.mapping = mapping;
        });
    }

    @property({attribute: false})
    mapping?: SAMLPropertyMapping;

    getSuccessMessage(): string {
        if (this.mapping) {
            return gettext("Successfully updated mapping.");
        } else {
            return gettext("Successfully created mapping.");
        }
    }

    send = (data: SAMLPropertyMapping): Promise<SAMLPropertyMapping> => {
        if (this.mapping) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlUpdate({
                pmUuid: this.mapping.pk || "",
                data: data
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.mapping?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("SAML Attribute Name")}
                ?required=${true}
                name="samlName">
                <input type="text" value="${ifDefined(this.mapping?.samlName)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">
                    ${gettext("Attribute name used for SAML Assertions. Can be a URN OID, a schema reference, or a any other string. If this property mapping is used for NameID Property, this field is discarded.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Friendly Name")}
                name="friendlyName">
                <input type="text" value="${ifDefined(this.mapping?.friendlyName)}" class="pf-c-form-control">
                <p class="pf-c-form__helper-text">
                    ${gettext("Optionally set the `FriendlyName` value of the Assertion attribute.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Expression")}
                name="expression">
                <ak-codemirror mode="python" value="${this.mapping?.expression}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    Expression using Python. See <a href="https://goauthentik.io/docs/property-mappings/expression/">here</a> for a list of all variables.
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
