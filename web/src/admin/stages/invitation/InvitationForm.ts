import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { dateTimeLocal, first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";
import YAML from "yaml";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";

import {
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    Invitation,
    StagesApi,
} from "@goauthentik/api";

@customElement("ak-invitation-form")
export class InvitationForm extends ModelForm<Invitation, string> {
    loadInstance(pk: string): Promise<Invitation> {
        return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsRetrieve({
            inviteUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated invitation.`;
        } else {
            return t`Successfully created invitation.`;
        }
    }

    async send(data: Invitation): Promise<Invitation> {
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsUpdate({
                inviteUuid: this.instance.pk || "",
                invitationRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesInvitationInvitationsCreate({
                invitationRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                ?slugMode=${true}
                label=${t`Name`}
                ?required=${true}
                name="name"
            >
                <input
                    type="text"
                    value="${this.instance?.name || ""}"
                    class="pf-c-form-control"
                    required
                    data-ak-slug="true"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Expires`} ?required=${true} name="expires">
                <input
                    type="datetime-local"
                    data-type="datetime-local"
                    class="pf-c-form-control"
                    required
                    value="${dateTimeLocal(first(this.instance?.expires, new Date()))}"
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Flow`} ?required=${true} name="flow">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Flow[]> => {
                        const args: FlowsInstancesListRequest = {
                            ordering: "slug",
                            designation: FlowsInstancesListDesignationEnum.Enrollment,
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const flows = await new FlowsApi(DEFAULT_CONFIG).flowsInstancesList(args);
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
                        return flow.pk === this.instance?.flow;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${t`When selected, the invite will only be usable with the flow. By default the invite is accepted on all flows with invitation stages.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Attributes`} name="fixedData">
                <ak-codemirror
                    mode="yaml"
                    value="${YAML.stringify(first(this.instance?.fixedData, {}))}"
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Optional data which is loaded into the flow's 'prompt_data' context variable. YAML or JSON.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="singleUse">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.singleUse, true)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${t`Single use`}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${t`When enabled, the invitation will be deleted after usage.`}
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
