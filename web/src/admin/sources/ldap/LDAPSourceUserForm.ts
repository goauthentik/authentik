import "#elements/forms/HorizontalFormElement";
import "#components/ak-text-input";
import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { userSource } from "#admin/common/search-sources";

import { LDAPSource, SourcesApi, UserLDAPSourceConnection } from "@goauthentik/api";

import { ifDefined } from "lit-html/directives/if-defined.js";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-ldap-user-form")
export class LDAPSourceUserForm extends ModelForm<UserLDAPSourceConnection, number> {
    @property({ attribute: false })
    source?: LDAPSource;

    public override getSuccessMessage(): string {
        return msg("Successfully connected user.");
    }

    protected async loadInstance(pk: number): Promise<UserLDAPSourceConnection> {
        return aki(SourcesApi).sourcesUserConnectionsLdapRetrieve({
            id: pk,
        });
    }

    async send(data: UserLDAPSourceConnection) {
        data.source = this.source?.pk || "";

        return aki(SourcesApi).sourcesUserConnectionsLdapCreate({
            userLDAPSourceConnectionRequest: data,
        });
    }

    renderForm() {
        return html`<ak-form-element-horizontal label=${msg("User")} name="user">
                ${AKSearchSelect({
                    name: "user",
                    source: userSource,
                    blankable: false,
                })}
            </ak-form-element-horizontal>
            <ak-text-input
                name="identifier"
                label=${msg("Identifier")}
                input-hint="code"
                required
                value="${ifDefined(this.instance?.identifier)}"
                help=${msg(
                    str`The unique identifier of this object in LDAP, the value of the '${this.source?.objectUniquenessField}' attribute.`,
                )}
            >
            </ak-text-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-source-ldap-user-form": LDAPSourceUserForm;
    }
}
