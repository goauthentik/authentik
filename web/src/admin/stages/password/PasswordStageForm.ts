import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    BackendsEnum,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    PasswordStage,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-stage-password-form")
export class PasswordStageForm extends ModelForm<PasswordStage, string> {
    loadInstance(pk: string): Promise<PasswordStage> {
        return new StagesApi(DEFAULT_CONFIG).stagesPasswordRetrieve({
            stageUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
        }
    }

    async send(data: PasswordStage): Promise<PasswordStage> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesPasswordUpdate({
                stageUuid: this.instance.pk || "",
                passwordStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesPasswordCreate({
                passwordStageRequest: data,
            });
        }
    }

    isBackendSelected(field: BackendsEnum): boolean {
        if (!this.instance) {
            return true;
        }
        return (
            this.instance.backends.filter((isField) => {
                return field === isField;
            }).length > 0
        );
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${msg("Validate the user's password against the selected backend(s).")}
            </div>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Backends")}
                        ?required=${true}
                        name="backends"
                    >
                        <select name="users" class="pf-c-form-control" multiple>
                            <option
                                value=${BackendsEnum.CoreAuthInbuiltBackend}
                                ?selected=${this.isBackendSelected(
                                    BackendsEnum.CoreAuthInbuiltBackend,
                                )}
                            >
                                ${msg("User database + standard password")}
                            </option>
                            <option
                                value=${BackendsEnum.CoreAuthTokenBackend}
                                ?selected=${this.isBackendSelected(
                                    BackendsEnum.CoreAuthTokenBackend,
                                )}
                            >
                                ${msg("User database + app passwords")}
                            </option>
                            <option
                                value=${BackendsEnum.SourcesLdapAuthLdapBackend}
                                ?selected=${this.isBackendSelected(
                                    BackendsEnum.SourcesLdapAuthLdapBackend,
                                )}
                            >
                                ${msg("User database + LDAP password")}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg("Selection of backends to test the password against.")}
                        </p>
                        <p class="pf-c-form__helper-text">
                            ${msg("Hold control/command to select multiple items.")}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Configuration flow")}
                        ?required=${true}
                        name="configureFlow"
                    >
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                                const args: FlowsInstancesListRequest = {
                                    ordering: "slug",
                                    designation:
                                        FlowsInstancesListDesignationEnum.StageConfiguration,
                                };
                                if (query !== undefined) {
                                    args.search = query;
                                }
                                const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(
                                    args,
                                );
                                return flows.results;
                            }}
                            .renderElement=${(flow: Flow): string => {
                                return RenderFlowOption(flow);
                            }}
                            .renderDescription=${(flow: Flow): TemplateResult => {
                                return html`${flow.name}`;
                            }}
                            .value=${(flow: Flow | undefined): string | undefined => {
                                return flow?.pk;
                            }}
                            .selected=${(flow: Flow): boolean => {
                                let selected = this.instance?.configureFlow === flow.pk;
                                if (
                                    !this.instance?.pk &&
                                    !this.instance?.configureFlow &&
                                    flow.slug === "default-password-change"
                                ) {
                                    selected = true;
                                }
                                return selected;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used by an authenticated user to configure their password. If empty, user will not be able to configure change their password.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Failed attempts before cancel")}
                        ?required=${true}
                        name="failedAttemptsBeforeCancel"
                    >
                        <input
                            type="number"
                            value="${first(this.instance?.failedAttemptsBeforeCancel, 5)}"
                            class="pf-c-form-control"
                            required
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "How many attempts a user has before the flow is canceled. To lock the user out, use a reputation policy and a user_write stage.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
