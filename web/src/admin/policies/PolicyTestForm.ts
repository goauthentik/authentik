import "#components/ak-status-label";
import "#elements/CodeMirror";
import "#elements/events/LogViewer";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import {
    CoreApi,
    CoreUsersListRequest,
    PoliciesApi,
    Policy,
    PolicyTestRequest,
    PolicyTestResult,
    User,
} from "@goauthentik/api";

import YAML from "yaml";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-policy-test-form")
export class PolicyTestForm extends Form<PolicyTestRequest> {
    public static verboseName = msg("Policy");
    public static verboseNamePlural = msg("Policies");
    public static createLabel = msg("Test");

    public override cancelable = true;

    public override size = PFSize.XLarge;

    static styles: CSSResult[] = [
        ...super.styles,
        PFDescriptionList,
        css`
            .ak-policy-test-log-messages {
                width: 100%;
            }
        `,
    ];

    #api = new PoliciesApi(DEFAULT_CONFIG);

    protected override formatSubmitLabel(submitLabel?: string | null): string {
        return submitLabel || msg("Run Test");
    }

    @property({ attribute: false })
    public policy: Policy | null = null;

    @state()
    protected result: PolicyTestResult | null = null;

    @property({ attribute: false })
    public request: PolicyTestRequest | null = null;

    public get verboseName(): string | null {
        return this.policy?.verboseName || null;
    }

    public get verboseNamePlural(): string | null {
        return this.policy?.verboseNamePlural || null;
    }

    public override reset(): void {
        super.reset();

        this.result = null;
    }

    public override getSuccessMessage(): string {
        return msg("Successfully sent test-request.");
    }

    protected override async send(data: PolicyTestRequest): Promise<PolicyTestResult> {
        this.request = data;

        this.result = await this.#api.policiesAllTestCreate({
            policyUuid: this.policy?.pk || "",
            policyTestRequest: data,
        });

        return this.result;
    }

    protected renderResult(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Passing")}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text">
                            <ak-status-label ?good=${this.result?.passing}></ak-status-label>
                        </span>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Messages")}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <ul>
                            ${(this.result?.messages || []).length > 0
                                ? this.result?.messages?.map((m) => {
                                      return html`<li>
                                          <span class="pf-c-form__label-text">${m}</span>
                                      </li>`;
                                  })
                                : html`<li>
                                      <span class="pf-c-form__label-text">-</span>
                                  </li>`}
                        </ul>
                    </div>
                </div>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal label=${msg("Log messages")}>
                <ak-log-viewer .items=${this.result?.logMessages}></ak-log-viewer>
            </ak-form-element-horizontal>`;
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("User")} required name="user">
                <ak-search-select
                    placeholder=${msg("Select a user...")}
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
                        return this.request?.user.toString() === user.pk.toString();
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>

            <ak-form-element-horizontal name="context">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "context",
                    },
                    msg("Context"),
                )}
                <ak-codemirror
                    id="context"
                    mode="yaml"
                    value=${YAML.stringify(this.request?.context ?? {})}
                >
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${msg("Set custom attributes using YAML or JSON.")}
                </p>
            </ak-form-element-horizontal>

            ${this.result ? this.renderResult() : null}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-test-form": PolicyTestForm;
    }
}
