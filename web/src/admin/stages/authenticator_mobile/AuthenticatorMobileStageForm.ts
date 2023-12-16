import { RenderFlowOption } from "@goauthentik/admin/flows/utils";
import { KeyUnknown } from "@goauthentik/app/elements/forms/Form";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/Alert";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";

import {
    AuthenticatorMobileStage,
    AuthenticatorMobileStageRequest,
    EnterpriseApi,
    Flow,
    FlowsApi,
    FlowsInstancesListDesignationEnum,
    FlowsInstancesListRequest,
    ItemMatchingModeEnum,
    LicenseSummary,
    StagesApi,
} from "@goauthentik/api";

const hostedCGWs: Map<string, string> = new Map([
    ["prod-eu-central-1.cgw.a7k.io", msg("authentik Enterprise eu-central-1")],
]);

@customElement("ak-stage-authenticator-mobile-form")
export class AuthenticatorMobileStageForm extends ModelForm<AuthenticatorMobileStage, string> {
    @state()
    showCustomCGWInput = false;

    @state()
    enterpriseStatus?: LicenseSummary;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFBanner);
    }

    async load(): Promise<void> {
        this.enterpriseStatus = await new EnterpriseApi(
            DEFAULT_CONFIG,
        ).enterpriseLicenseSummaryRetrieve();
    }

    async loadInstance(pk: string): Promise<AuthenticatorMobileStage> {
        const instance = await new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorMobileRetrieve({
            stageUuid: pk,
        });
        this.showCustomCGWInput = !hostedCGWs.has(instance.cgwEndpoint);
        return instance;
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated stage.");
        } else {
            return msg("Successfully created stage.");
        }
    }

    async send(data: AuthenticatorMobileStage): Promise<AuthenticatorMobileStage> {
        if (this.showCustomCGWInput) {
            data.cgwEndpoint = (data as unknown as KeyUnknown)["customCgwEndpoint"] as string;
        }
        if (this.instance) {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorMobilePartialUpdate({
                stageUuid: this.instance.pk || "",
                patchedAuthenticatorMobileStageRequest: data,
            });
        } else {
            return new StagesApi(DEFAULT_CONFIG).stagesAuthenticatorMobileCreate({
                authenticatorMobileStageRequest: data as unknown as AuthenticatorMobileStageRequest,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`
            <div class="pf-c-banner pf-m-info" slot="above-form">
                ${msg("Mobile stage is in preview.")}
                <a href="mailto:hello@goauthentik.io">${msg("Send us feedback!")}</a>
            </div>
            <div class="form-help-text">
                ${msg(
                    "Stage used to configure a mobile-based authenticator. This stage should be used for configuration flows.",
                )}
            </div>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${first(this.instance?.name, "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Authenticator type name")}
                ?required=${false}
                name="friendlyName"
            >
                <input
                    type="text"
                    value="${first(this.instance?.friendlyName, "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Display name of this authenticator, used by users when they enroll an authenticator.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Stage-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("User decision mode")}
                        ?required=${true}
                        name="itemMatchingMode"
                    >
                        <ak-radio
                            .options=${[
                                {
                                    label: msg("Accept/Deny"),
                                    value: ItemMatchingModeEnum.AcceptDeny,
                                },
                                {
                                    label: msg("Number matching (2 digit numbers)"),
                                    value: ItemMatchingModeEnum.NumberMatching2,
                                },
                                {
                                    label: msg("Number matching (3 digit numbers)"),
                                    value: ItemMatchingModeEnum.NumberMatching3,
                                    default: true,
                                },
                            ]}
                            .value=${this.instance?.itemMatchingMode}
                        >
                        </ak-radio>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Cloud Gateway endpoint")}
                        ?required=${false}
                        name="cgwEndpoint"
                    >
                        <ak-radio
                            @change=${(ev: CustomEvent<{ value: string }>) => {
                                this.showCustomCGWInput = !hostedCGWs.has(ev.detail.value);
                            }}
                            .options=${[
                                ...Array.from(hostedCGWs, ([endpoint, label]) => {
                                    return {
                                        label: label,
                                        value: endpoint,
                                    };
                                }),
                                {
                                    label: msg("Custom Endpoint"),
                                    value: hostedCGWs.has(this.instance?.cgwEndpoint || "")
                                        ? false
                                        : this.instance?.cgwEndpoint,
                                },
                            ]}
                            .value=${this.instance?.cgwEndpoint}
                        >
                        </ak-radio>
                        ${!this.showCustomCGWInput ?? !this.enterpriseStatus?.valid
                            ? html`
                                  <ak-alert ?inline=${true}>
                                      ${msg("Hosted cloud gateways require authentik Enterprise.")}
                                  </ak-alert>
                              `
                            : html``}
                    </ak-form-element-horizontal>
                    ${this.showCustomCGWInput
                        ? html`<ak-form-element-horizontal
                              label=${msg("Custom Cloud Gateway endpoint")}
                              ?required=${false}
                              name="customCgwEndpoint"
                          >
                              <input
                                  type="text"
                                  value="${first(this.instance?.cgwEndpoint, "")}"
                                  class="pf-c-form-control"
                              />
                          </ak-form-element-horizontal>`
                        : nothing}
                    <ak-form-element-horizontal
                        label=${msg("Configuration flow")}
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
                                return this.instance?.configureFlow === flow.pk;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Flow used by an authenticated user to configure this Stage. If empty, user will not be able to configure this stage.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        `;
    }
}
