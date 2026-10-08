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

import { renderDialog } from "#elements/dialogs";
import { ModelForm } from "#elements/forms/ModelForm";
import { settleFormFields } from "#elements/forms/settle-form-fields";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { eventTransportsProvider, eventTransportsSelector } from "#admin/events/RuleFormHelpers";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";
import "#admin/lifecycle/UserExpirationRulePreview";

import {
    ActivityBasisEnum,
    CoreApi,
    CoreGroupsListRequest,
    Group,
    LifecycleApi,
    OffboardingActionEnum,
    UserExpirationRule,
    UserExpirationRuleRequest,
    UserTypeEnum,
} from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
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

    public constructor() {
        super();
        // Form.submit is an instance callback rather than a prototype method.
        const submit = this.submit;

        this.submit = async <T = unknown>(event: SubmitEvent): Promise<T | false> => {
            event.preventDefault();

            if (this.form) {
                await settleFormFields(this.form);
            }

            if (!this.reportValidity()) {
                return false;
            }

            const data = this.toRequest(this.toJSON());

            if (this.requiresDeleteConfirmation(data)) {
                let confirmed = false;

                const close = (click: Event) => {
                    const button = click.currentTarget as HTMLButtonElement;
                    button.closest("ak-modal")?.close(button.value);
                };

                await renderDialog(
                    html`<ak-modal
                        headline=${msg("Confirm account deletion", {
                            id: "user-expiration.delete-confirmation.title",
                        })}
                    >
                        <p>
                            ${msg(str`Save "${data.name}" as an enabled delete rule?`, {
                                id: "user-expiration.delete-confirmation.description",
                            })}
                        </p>
                        <p>
                            ${msg(
                                "This can permanently delete matching accounts, including users with an offboarding already scheduled. Deleted accounts cannot be restored.",
                                { id: "user-expiration.delete-confirmation.warning" },
                            )}
                        </p>
                        ${
                            this.instance?.pk
                                ? html`<p>
                                      ${msg("Preview your changes before proceeding.", {
                                          id: "user-expiration.delete-confirmation.preview.description",
                                      })}
                                  </p>`
                                : nothing
                        }
                        <button
                            slot="actions"
                            class="pf-c-button pf-m-secondary"
                            type="button"
                            value="cancel"
                            autofocus
                            @click=${close}
                        >
                            ${msg("Cancel", { id: "common.actions.cancel" })}
                        </button>
                        <button
                            slot="actions"
                            class="pf-c-button pf-m-danger"
                            type="button"
                            value="confirmed"
                            @click=${close}
                        >
                            ${msg("Save delete rule", {
                                id: "user-expiration.delete-confirmation.submit",
                            })}
                        </button>
                    </ak-modal>`,
                    {
                        invokerElement: this,
                        onDispose: (closeEvent) => {
                            confirmed =
                                closeEvent?.target instanceof HTMLDialogElement &&
                                closeEvent.target.returnValue === "confirmed";
                        },
                    },
                );

                if (!confirmed) {
                    return false;
                }
            }

            return submit<T>(event);
        };
    }

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

    protected toRequest(data: UserExpirationRule): UserExpirationRuleRequest {
        // An empty warning period means "no warning", and an empty group means "every
        // user". The API expects null for both, not the empty string the blank
        // selections serialize to.
        return {
            ...data,
            group: data.group || null,
            warnBefore: data.warnBefore || null,
        };
    }

    protected requiresDeleteConfirmation(data: UserExpirationRuleRequest): boolean {
        if (!data.enabled || data.action !== OffboardingActionEnum.Delete) {
            return false;
        }

        if (!this.instance?.enabled || this.instance.action !== OffboardingActionEnum.Delete) {
            return true;
        }

        const saved = this.toRequest(this.instance);

        // A different group may include new users; moving from all users to a
        // group only narrows the scope. Type ordering does not affect the scope.
        const scopeExpanded =
            Boolean(saved.group && data.group !== saved.group) ||
            Boolean(data.userTypes?.some((type) => !saved.userTypes?.includes(type))) ||
            Boolean(saved.excludeSuperusers && !data.excludeSuperusers);

        // Clock and policy changes can affect users differently. Confirm them
        // without trying to reproduce backend activity or policy evaluation here.
        const expirationChanged = (
            ["activityBasis", "inactivityDuration", "warnBefore", "policyEngineMode"] as const
        ).some((field) => data[field] !== saved[field]);

        return scopeExpanded || expirationChanged;
    }

    protected override async send(data: UserExpirationRule): Promise<UserExpirationRule> {
        const request = this.toRequest(data);

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

        return html`${
                this.instance?.pk
                    ? html`<ak-user-expiration-rule-preview
                          .rule=${this.instance}
                          .getRequest=${() => this.toRequest(this.toJSON())}
                      >
                          <button slot="trigger" class="pf-c-button pf-m-secondary" type="button">
                              ${msg("Preview changes", {
                                  id: "user-expiration.form.preview.label",
                              })}
                          </button>
                      </ak-user-expiration-rule-preview>`
                    : nothing
            }
            <ak-text-input
                label=${msg("Name", { id: "user-expiration.field.name.label" })}
                name="name"
                required
                value=${ifDefined(this.instance?.name)}
                placeholder=${msg("Type a name for this expiration rule...", {
                    id: "user-expiration.field.name.placeholder",
                })}
                ?autofocus=${!this.instance}
            ></ak-text-input>

            <ak-radio-input
                label=${msg("Activity basis", {
                    id: "user-expiration.field.activity-basis.label",
                })}
                name="activityBasis"
                required
                .value=${this.instance?.activityBasis ?? ActivityBasisEnum.SuccessfulEvents}
                .options=${[
                    {
                        label: msg("Last login", {
                            id: "user-expiration.activity-basis.last-login.label",
                        }),
                        value: ActivityBasisEnum.LastLogin,
                        description: html`${msg("Use the user's recorded last login.", {
                            id: "user-expiration.activity-basis.last-login.description",
                        })}`,
                    },
                    {
                        label: msg("Last activity", {
                            id: "user-expiration.activity-basis.successful-events.label",
                        }),
                        value: ActivityBasisEnum.SuccessfulEvents,
                        default: true,
                        description: html`${msg(
                            "Also count successful authentication, application authorization, and OAuth refreshes. Failed requests and API-token requests do not count. Refresh activity includes a 24-hour allowance before expiration.",
                            { id: "user-expiration.activity-basis.successful-events.description" },
                        )}`,
                    },
                ]}
                help=${msg(
                    "Event retention defaults to 365 days. For Last activity, retain events for at least the inactivity duration plus 24 hours. Increasing retention cannot recover deleted events. Preview the effect before changing this setting.",
                    { id: "user-expiration.field.activity-basis.description" },
                )}
            ></ak-radio-input>

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
                        "Only expire users of these types. Service accounts are excluded by default. API-token requests do not count as activity.",
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
                    "How long a user may be inactive before they expire, using the selected activity basis. The account creation date is the baseline for users who have never been active.",
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
            ></ak-radio-input>

            <ak-switch-input
                name="enabled"
                label=${msg("Enabled", { id: "user-expiration.field.enabled.label" })}
                ?checked=${this.instance?.enabled ?? false}
                help=${msg(
                    "New rules start disabled so you can preview them and bind policies before enabling them. Disabling a rule stops expiration and removes its pending offboardings shortly after saving.",
                    {
                        id: "user-expiration.field.enabled.description",
                    },
                )}
            ></ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-expiration-rule-form": UserExpirationRuleForm;
    }
}
