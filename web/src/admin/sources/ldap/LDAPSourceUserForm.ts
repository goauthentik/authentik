import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";

import { AKLabel } from "#components/ak-label";

import {
    CoreApi,
    CoreUsersListRequest,
    LDAPSource,
    SourcesApi,
    User,
    UserLDAPSourceConnection,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { ifDefined } from "lit-html/directives/if-defined.js";
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
        return html`<ak-form-element-horizontal name="user">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "user",
                    },
                    msg("User"),
                )}
                <ak-search-select
                    id="user"
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await aki(CoreApi).coreUsersList(args);
                        return users.results;
                    }}
                    .renderElement=${(user: User): string => {
                        return user.username;
                    }}
                    .renderDescription=${(user: User): TemplateResult => {
                        return html`${user.name}`;
                    }}
                    .value=${(user: User | undefined): number | undefined => {
                        return user?.pk;
                    }}
                >
                </ak-search-select>
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
