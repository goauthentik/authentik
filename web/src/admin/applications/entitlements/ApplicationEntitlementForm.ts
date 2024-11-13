import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-toggle-group";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";



import { msg } from "@lit/localize";
import { CSSResult } from "lit";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";



import PFContent from "@patternfly/patternfly/components/Content/content.css";



import { ApplicationEntitlement, CoreApi, CoreGroupsListRequest, CoreUsersListRequest, Group, User } from "@goauthentik/api";


enum target {
    group = "group",
    user = "user",
}

@customElement("ak-application-entitlement-form")
export class ApplicationEntitlementForm extends ModelForm<ApplicationEntitlement, string> {
    async loadInstance(pk: string): Promise<ApplicationEntitlement> {
        const binding = await new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsRetrieve({
            appEntitlementUuid: pk,
        });
        if (binding?.groupObj) {
            this.policyGroupUser = target.group;
        }
        if (binding?.userObj) {
            this.policyGroupUser = target.user;
        }
        return binding;
    }

    @property()
    targetPk?: string;

    @state()
    policyGroupUser: target = target.group;

    getSuccessMessage(): string {
        if (this.instance?.appEntitlementUuid) {
            return msg("Successfully updated entitlement.");
        } else {
            return msg("Successfully created entitlement.");
        }
    }

    static get styles(): CSSResult[] {
        return [...super.styles, PFContent];
    }

    send(data: ApplicationEntitlement): Promise<unknown> {
        if (this.targetPk) {
            data.app = this.targetPk;
        }
        switch (this.policyGroupUser) {
            case target.group:
                data.user = null;
                break;
            case target.user:
                data.group = null;
                break;
        }

        if (this.instance?.appEntitlementUuid) {
            return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsUpdate({
                appEntitlementUuid: this.instance.appEntitlementUuid || "",
                applicationEntitlementRequest: data,
            });
        } else {
            return new CoreApi(DEFAULT_CONFIG).coreApplicationEntitlementsCreate({
                applicationEntitlementRequest: data,
            });
        }
    }

    renderModeSelector(): TemplateResult {
        return html` <ak-toggle-group
            value=${this.policyGroupUser}
            @ak-toggle=${(ev: CustomEvent<{ value: target }>) => {
                this.policyGroupUser = ev.detail.value;
            }}
        >
            <option value=${target.group}>${msg("Group")}</option>
            <option value=${target.user}>${msg("User")}</option>
        </ak-toggle-group>`;
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <div class="pf-c-card pf-m-selectable pf-m-selected">
                <div class="pf-c-card__body">${this.renderModeSelector()}</div>
                <div class="pf-c-card__footer">
                    <ak-form-element-horizontal
                        label=${msg("Group")}
                        name="group"
                        ?hidden=${this.policyGroupUser !== target.group}
                    >
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Group[]> => {
                                const args: CoreGroupsListRequest = {
                                    ordering: "name",
                                    includeUsers: false,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(
                                    args,
                                );
                                return groups.results;
                            }}
                            .renderElement=${(group: Group): string => {
                                return group.name;
                            }}
                            .value=${(group: Group | undefined): string | undefined => {
                                return group?.pk;
                            }}
                            .selected=${(group: Group): boolean => {
                                return group.pk === this.instance?.group;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("User")}
                        name="user"
                        ?hidden=${this.policyGroupUser !== target.user}
                    >
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<User[]> => {
                                const args: CoreUsersListRequest = {
                                    ordering: "username",
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(args);
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
                            .selected=${(user: User): boolean => {
                                return user.pk === this.instance?.user;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                    </ak-form-element-horizontal>
                </div>
            </div>
            <ak-form-element-horizontal
                label=${msg("Attributes")}
                ?required=${false}
                name="attributes"
            >
                <ak-codemirror
                    mode=${CodeMirrorMode.YAML}
                    value="${YAML.stringify(first(this.instance?.attributes, {}))}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-entitlement-form": ApplicationEntitlementForm;
    }
}
