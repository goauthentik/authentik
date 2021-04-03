import { LDAPSource, SourcesApi, PropertymappingsApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import "../../../elements/forms/FormGroup";
import "../../../elements/forms/HorizontalFormElement";
import { ifDefined } from "lit-html/directives/if-defined";
import { until } from "lit-html/directives/until";

@customElement("ak-source-ldap-form")
export class LDAPSourceForm extends Form<LDAPSource> {

    set sourceSlug(value: string) {
        new SourcesApi(DEFAULT_CONFIG).sourcesLdapRead({
            slug: value,
        }).then(source => {
            this.source = source;
        });
    }

    @property({attribute: false})
    source?: LDAPSource;

    getSuccessMessage(): string {
        if (this.source) {
            return t`Successfully updated source.`;
        } else {
            return t`Successfully created source.`;
        }
    }

    send = (data: LDAPSource): Promise<LDAPSource> => {
        if (this.source) {
            return new SourcesApi(DEFAULT_CONFIG).sourcesLdapUpdate({
                slug: this.source.slug,
                data: data
            });
        } else {
            return new SourcesApi(DEFAULT_CONFIG).sourcesLdapCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.source?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Slug`}
                ?required=${true}
                name="slug">
                <input type="text" value="${ifDefined(this.source?.slug)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="enabled">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.source?.enabled || true}>
                    <label class="pf-c-check__label">
                        ${t`Enabled`}
                    </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="syncUsers">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.source?.syncUsers || true}>
                    <label class="pf-c-check__label">
                        ${t`Sync users`}
                    </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="syncUsersPassword">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.source?.syncUsersPassword || true}>
                    <label class="pf-c-check__label">
                        ${t`Sync users' passwords`}
                    </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="syncGroups">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.source?.syncGroups || true}>
                    <label class="pf-c-check__label">
                        ${t`Sync groups`}
                    </label>
                </div>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Connection settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Server URI`}
                        ?required=${true}
                        name="serverUri">
                        <input type="text" value="${ifDefined(this.source?.serverUri)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal name="startTls">
                        <div class="pf-c-check">
                            <input type="checkbox" class="pf-c-check__input" ?checked=${this.source?.startTls || true}>
                            <label class="pf-c-check__label">
                                ${t`Enable StartTLS`}
                            </label>
                        </div>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Bind CN`}
                        ?required=${true}
                        name="bindCn">
                        <input type="text" value="${ifDefined(this.source?.bindCn)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Bind Password`}
                        ?required=${true}
                        name="bindPassword">
                        <input type="text" value="${ifDefined(this.source?.bindPassword)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Base DN`}
                        ?required=${true}
                        name="baseDn">
                        <input type="text" value="${ifDefined(this.source?.baseDn)}" class="pf-c-form-control" required>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
            <ak-form-group>
                <span slot="header">
                    ${t`Advanced settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`User Property Mappings`}
                        ?required=${true}
                        name="propertyMappings">
                        <select class="pf-c-form-control" multiple>
                            ${until(new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapList({
                                ordering: "object_field"
                            }).then(mappings => {
                                return mappings.results.map(mapping => {
                                    let selected = false;
                                    if (!this.source?.propertyMappings) {
                                        selected = mapping.managed?.startsWith("goauthentik.io/sources/ldap/default") || mapping.managed?.startsWith("goauthentik.io/sources/ldap/ms") || false;
                                    } else {
                                        selected = Array.from(this.source?.propertyMappings).some(su => {
                                            return su == mapping.pk;
                                        });
                                    }
                                    return html`<option value=${ifDefined(mapping.pk)} ?selected=${selected}>${mapping.name}</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Property mappings used to user creation.`}</p>
                        <p class="pf-c-form__helper-text">${t`Hold control/command to select multiple items.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Group Property Mappings`}
                        ?required=${true}
                        name="propertyMappingsGroup">
                        <select class="pf-c-form-control" multiple>
                            ${until(new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapList({
                                ordering: "object_field"
                            }).then(mappings => {
                                return mappings.results.map(mapping => {
                                    let selected = false;
                                    if (!this.source?.propertyMappingsGroup) {
                                        selected = mapping.managed === "goauthentik.io/sources/ldap/default-name";
                                    } else {
                                        selected = Array.from(this.source?.propertyMappingsGroup).some(su => {
                                            return su == mapping.pk;
                                        });
                                    }
                                    return html`<option value=${ifDefined(mapping.pk)} ?selected=${selected}>${mapping.name}</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Property mappings used to group creation.`}</p>
                        <p class="pf-c-form__helper-text">${t`Hold control/command to select multiple items.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Addition User DN`}
                        name="additionalUserDn">
                        <input type="text" value="${ifDefined(this.source?.additionalUserDn)}" class="pf-c-form-control">
                        <p class="pf-c-form__helper-text">${t`Additional user DN, prepended to the Base DN.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Addition Group DN`}
                        name="additionalGroupDn">
                        <input type="text" value="${ifDefined(this.source?.additionalGroupDn)}" class="pf-c-form-control">
                        <p class="pf-c-form__helper-text">${t`Additional group DN, prepended to the Base DN.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`User object filter`}
                        ?required=${true}
                        name="userObjectFilter">
                        <input type="text" value="${this.source?.userObjectFilter || "(objectClass=person)"}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`Consider Objects matching this filter to be Users.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Group object filter`}
                        ?required=${true}
                        name="groupObjectFilter">
                        <input type="text" value="${this.source?.groupObjectFilter || "(objectClass=group)"}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`Consider Objects matching this filter to be Groups.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Group membership field`}
                        ?required=${true}
                        name="groupMembershipField">
                        <input type="text" value="${this.source?.groupMembershipField || "member"}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`Field which contains members of a group.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Object uniqueness field`}
                        ?required=${true}
                        name="objectUniquenessField">
                        <input type="text" value="${this.source?.objectUniquenessField || "objectSid"}" class="pf-c-form-control" required>
                        <p class="pf-c-form__helper-text">${t`Field which contains a unique Identifier.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
