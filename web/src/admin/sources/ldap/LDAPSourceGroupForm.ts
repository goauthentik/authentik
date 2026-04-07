import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";

import {
    CoreApi,
    CoreGroupsListRequest,
    Group,
    GroupLDAPSourceConnection,
    LDAPSource,
    SourcesApi,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-source-ldap-group-form")
export class LDAPSourceGroupForm extends ModelForm<GroupLDAPSourceConnection, number> {
    @property({ attribute: false })
    source?: LDAPSource;

    public override getSuccessMessage(): string {
        return msg("Successfully connected user.");
    }

    protected async loadInstance(pk: number): Promise<GroupLDAPSourceConnection> {
        return new SourcesApi(DEFAULT_CONFIG).sourcesGroupConnectionsLdapRetrieve({
            id: pk,
        });
    }

    async send(data: GroupLDAPSourceConnection) {
        data.source = this.source?.pk || "";
        return new SourcesApi(DEFAULT_CONFIG).sourcesGroupConnectionsLdapCreate({
            groupLDAPSourceConnectionRequest: data,
        });
    }

    renderForm() {
        return html`<ak-form-element-horizontal label=${msg("Group")} name="group">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Group[]> => {
                        const args: CoreGroupsListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);
                        return groups.results;
                    }}
                    .renderElement=${(group: Group): string => {
                        return group.name;
                    }}
                    .value=${(group: Group | undefined): string | undefined => {
                        return group?.pk;
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
        "ak-source-ldap-group-form": LDAPSourceGroupForm;
    }
}
