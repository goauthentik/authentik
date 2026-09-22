import "#elements/ak-checkbox-group/ak-checkbox-group";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";
import "#elements/utils/TimeDeltaHelp";
import "#components/ak-radio-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import { aki } from "#common/api/client";
import { userTypeToLabel } from "#common/labels";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { eventTransportsProvider, eventTransportsSelector } from "#admin/events/RuleFormHelpers";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import {
    CoreApi,
    CoreGroupsListRequest,
    Group,
    LifecycleApi,
    OffboardingActionEnum,
    UserExpirationRule,
    UserExpirationRuleRequest,
    UserTypeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

// Internal service accounts are never expired, so they are not offered. The backend
// rejects them too.
const SELECTABLE_USER_TYPES: UserTypeEnum[] = [
    UserTypeEnum.Internal,
    UserTypeEnum.External,
    UserTypeEnum.ServiceAccount,
];

/**
 * Create or edit a rule that expires users after a period of inactivity.
 */
@customElement("ak-user-expiration-rule-form")
export class UserExpirationRuleForm extends ModelForm<UserExpirationRule, string> {
    public static override verboseName = msg("User Expiration Rule", {
        id: "user-expiration.form.verbose-name",
    });

    public static override verboseNamePlural = msg("User Expiration Rules", {
        id: "user-expiration.form.verbose-name-plural",
    });

    #api = aki(LifecycleApi);

    protected async loadInstance(pk: string): Promise<UserExpirationRule> {
        return this.#api.lifecycleUserExpirationRulesRetrieve({ id: pk });
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated expiration rule.", {
                  id: "user-expiration.form.update.success",
              })
            : msg("Successfully created expiration rule.", {
                  id: "user-expiration.form.create.success",
              });
    }

    protected override async send(data: UserExpirationRule): Promise<UserExpirationRule> {
        // An empty warning period means "no warning", and an empty group means "every
        // user". The API expects null for both, not the empty string the blank
        // selections serialize to.
        const request = {
            ...data,
            group: data.group || null,
            warnBefore: data.warnBefore || null,
        } as unknown as UserExpirationRuleRequest;

        if (this.instance?.pk) {
            return this.#api.lifecycleUserExpirationRulesUpdate({
                id: this.instance.pk,
                userExpirationRuleRequest: request,
            });
        }

        return this.#api.lifecycleUserExpirationRulesCreate({
            userExpirationRuleRequest: request,
        });
    }

    #fetchGroups = async (query?: string): Promise<Group[]> => {
        const args: CoreGroupsListRequest = {
            ordering: "name",
            includeUsers: false,
        };

        if (query !== undefined) {
            args.search = query;
        }

        const groups = await aki(CoreApi).coreGroupsList(args);

        return groups.results;
    };

    protected override renderForm(): SlottedTemplateResult {
        const selectedUserTypes = this.instance?.userTypes ?? [
            UserTypeEnum.Internal,
            UserTypeEnum.External,
        ];

        return html`<ak-text-input
                label=${msg("Name", { id: "user-expiration.field.name.label" })}
                name="name"
                required
                value=${ifDefined(this.instance?.name)}
                placeholder=${msg("Type a name for this expiration rule...", {
                    id: "user-expiration.field.name.placeholder",
                })}
                ?autofocus=${!this.instance}
            ></ak-text-input>

            <ak-switch-input
                name="enabled"
                label=${msg("Enabled", { id: "user-expiration.field.enabled.label" })}
                ?checked=${this.instance?.enabled ?? true}
                help=${msg(
                    "A disabled rule expires nobody and cancels the expirations it has already scheduled.",
                    {
                        id: "user-expiration.field.enabled.description",
                    },
                )}
            ></ak-switch-input>

            <ak-form-element-horizontal
                label=${msg("Group", { id: "user-expiration.field.group.label" })}
                name="group"
            >
                <ak-search-select
                    .fetchObjects=${this.#fetchGroups}
                    .renderElement=${(group: Group): string => group.name}
                    .value=${(group: Group | undefined): string | undefined => group?.pk}
                    .selected=${(group: Group): boolean => group.pk === this.instance?.group}
                    blankable
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Only expire members of this group, including members of its child groups. Leave empty to apply the rule to every user.",
                        { id: "user-expiration.field.group.description" },
                    )}
                </p>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal required name="userTypes">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "user-expiration-user-types",
                        required: true,
                    },
                    msg("User types", { id: "user-expiration.field.user-types.label" }),
                )}
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Only expire users of these types. Signing in with a token does not count as activity, so service accounts are excluded by default.",
                        { id: "user-expiration.field.user-types.description" },
                    )}
                </p>
                <ak-checkbox-group
                    id="user-expiration-user-types"
                    .options=${SELECTABLE_USER_TYPES.map((type) => ({
                        name: type,
                        label: userTypeToLabel(type),
                    }))}
                    .value=${selectedUserTypes.filter((type) =>
                        SELECTABLE_USER_TYPES.includes(type),
                    )}
                ></ak-checkbox-group>
            </ak-form-element-horizontal>

            <ak-text-input
                label=${msg("Inactivity duration", {
                    id: "user-expiration.field.inactivity-duration.label",
                })}
                name="inactivityDuration"
                required
                value=${this.instance?.inactivityDuration || "days=90"}
                input-hint="code"
                help=${msg(
                    "How long a user may go without signing in before they are expired. Measured from their last login, or from the date they were created if they have never signed in.",
                    { id: "user-expiration.field.inactivity-duration.description" },
                )}
                .bighelp=${html`<ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            ></ak-text-input>

            <ak-radio-input
                label=${msg("Action", { id: "offboarding.field.action.label" })}
                name="action"
                required
                .value=${this.instance?.action ?? OffboardingActionEnum.Deactivate}
                .options=${[
                    {
                        label: msg("Deactivate", { id: "offboarding.action.deactivate.label" }),
                        value: OffboardingActionEnum.Deactivate,
                        default: true,
                        description: html`${msg(
                            "Lock the user out of authentik without removing their account.",
                            { id: "offboarding.action.deactivate.description" },
                        )}`,
                    },
                    {
                        label: msg("Delete", { id: "offboarding.action.delete.label" }),
                        value: OffboardingActionEnum.Delete,
                        description: html`${msg("Permanently delete the user's account.", {
                            id: "offboarding.action.delete.description",
                        })}`,
                    },
                ]}
            ></ak-radio-input>

            <ak-switch-input
                name="revokeSessions"
                label=${msg("Revoke sessions", { id: "offboarding.field.revoke-sessions.label" })}
                ?checked=${this.instance?.revokeSessions ?? true}
                help=${msg("Revoke all of the user's sessions when offboarding.", {
                    id: "offboarding.field.revoke-sessions.description",
                })}
            ></ak-switch-input>

            <ak-switch-input
                name="revokeTokens"
                label=${msg("Revoke tokens", { id: "offboarding.field.revoke-tokens.label" })}
                ?checked=${this.instance?.revokeTokens ?? true}
                help=${msg("Revoke all of the user's tokens when offboarding.", {
                    id: "offboarding.field.revoke-tokens.description",
                })}
            ></ak-switch-input>

            <ak-switch-input
                name="excludeSuperusers"
                label=${msg("Exclude superusers", {
                    id: "user-expiration.field.exclude-superusers.label",
                })}
                ?checked=${this.instance?.excludeSuperusers ?? true}
                help=${msg("Never expire members of a superuser group.", {
                    id: "user-expiration.field.exclude-superusers.description",
                })}
            ></ak-switch-input>

            <ak-text-input
                label=${msg("Warning period", {
                    id: "user-expiration.field.warn-before.label",
                })}
                name="warnBefore"
                value=${ifDefined(this.instance?.warnBefore ?? undefined)}
                input-hint="code"
                placeholder=${msg("e.g. days=7", {
                    id: "user-expiration.field.warn-before.placeholder",
                })}
                help=${msg(
                    "Schedule the offboarding and notify the user this long before they expire. Leave empty to expire users without warning. Must be shorter than the inactivity duration.",
                    { id: "user-expiration.field.warn-before.description" },
                )}
                .bighelp=${html`<ak-utils-time-delta-help></ak-utils-time-delta-help>`}
            ></ak-text-input>

            <ak-form-element-horizontal
                label=${msg("Notification transports", {
                    id: "user-expiration.field.notification-transports.label",
                })}
                name="notificationTransports"
            >
                <ak-dual-select-dynamic-selected
                    .provider=${eventTransportsProvider}
                    .selector=${eventTransportsSelector(this.instance?.notificationTransports)}
                    available-label=${msg("Available Transports", {
                        id: "user-expiration.field.notification-transports.available-label",
                    })}
                    selected-label=${msg("Selected Transports", {
                        id: "user-expiration.field.notification-transports.selected-label",
                    })}
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select which transports should be used to warn the user. If none are selected, the notification is only shown in the authentik UI.",
                        { id: "user-expiration.field.notification-transports.description" },
                    )}
                </p>
            </ak-form-element-horizontal>

            <ak-radio-input
                label=${msg("Policy engine mode", {
                    id: "user-expiration.field.policy-engine-mode.label",
                })}
                name="policyEngineMode"
                required
                .value=${this.instance?.policyEngineMode}
                .options=${policyEngineModes}
                help=${msg(
                    "How the policies bound to this rule are combined. A user is only expired if they pass them.",
                    { id: "user-expiration.field.policy-engine-mode.description" },
                )}
            ></ak-radio-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-expiration-rule-form": UserExpirationRuleForm;
    }
}
