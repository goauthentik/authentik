import { BasePolicyForm } from "@goauthentik/admin/policies/BasePolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import { me } from "@goauthentik/common/users";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import YAML from "yaml";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFStack from "@patternfly/patternfly/layouts/Stack/stack.css";

import {
    CoreApi,
    CoreUsersListRequest,
    ExpressionPolicy,
    PoliciesApi,
    PolicyTestResult,
    ResponseError,
    SessionUser,
    User,
    ValidationErrorFromJSON,
} from "@goauthentik/api";

@customElement("ak-policy-expression-form")
export class ExpressionPolicyForm extends BasePolicyForm<ExpressionPolicy> {
    @property({ type: Boolean })
    showPreview = true;

    @state()
    preview?: PolicyTestResult;

    @state()
    previewError?: string[];

    @state()
    user?: SessionUser;

    @state()
    previewLoading = false;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFGrid, PFStack, PFTitle);
    }

    async loadInstance(pk: string): Promise<ExpressionPolicy> {
        const policy = await new PoliciesApi(DEFAULT_CONFIG).policiesExpressionRetrieve({
            policyUuid: pk,
        });
        this.user = await me();
        await this.refreshPreview(policy);
        return policy;
    }

    async send(data: ExpressionPolicy): Promise<ExpressionPolicy> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionUpdate({
                policyUuid: this.instance.pk || "",
                expressionPolicyRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionCreate({
                expressionPolicyRequest: data,
            });
        }
    }

    _shouldRefresh = false;
    _timer = 0;

    connectedCallback(): void {
        super.connectedCallback();
        if (!this.showPreview) {
            return;
        }
        // Only check if we should update once a second, to prevent spamming API requests
        // when many fields are edited
        const minUpdateDelay = 1000;
        this._timer = setInterval(() => {
            if (this._shouldRefresh) {
                this.refreshPreview();
                this._shouldRefresh = false;
            }
        }, minUpdateDelay) as unknown as number;
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        if (!this.showPreview) {
            return;
        }
        clearTimeout(this._timer);
    }

    async refreshPreview(policy?: ExpressionPolicy): Promise<void> {
        if (!policy) {
            policy = this.serializeForm();
            if (!policy) {
                return;
            }
        }
        this.previewLoading = true;
        try {
            interface testpolicy {
                expression: string;
                user?: number;
                context?: { [key: string]: unknown };
            }
            const tp = policy as unknown as testpolicy;
            this.preview = await new PoliciesApi(DEFAULT_CONFIG).policiesExpressionTestCreate({
                expressionPolicyTestRequest: {
                    expression: tp.expression,
                    user: tp.user || this.user?.user.pk || 0,
                    context: tp.context || {},
                },
                policyUuid: this.instancePk || "",
            });
            this.previewError = undefined;
        } catch (exc) {
            const errorMessage = ValidationErrorFromJSON(
                await (exc as ResponseError).response.json(),
            );
            this.previewError = errorMessage.nonFieldErrors;
        } finally {
            this.previewLoading = false;
        }
    }

    renderForm(): TemplateResult {
        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-l-grid__item pf-m-6-col pf-l-stack">
                <div class="pf-c-form pf-m-horizontal pf-l-stack__item">
                    ${this.renderEditForm()}
                </div>
            </div>
            <div class="pf-l-grid__item pf-m-6-col">${this.renderPreview()}</div>
        </div> `;
    }

    renderPreview(): TemplateResult {
        return html`
            <div class="pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">${msg("Test parameters")}</div>
                    <div class="pf-c-card__body pf-c-form pf-m-horizontal">
                        <ak-form-element-horizontal label=${msg("User")} name="user">
                            <ak-search-select
                                .fetchObjects=${async (query?: string): Promise<User[]> => {
                                    const args: CoreUsersListRequest = {
                                        ordering: "username",
                                    };
                                    if (query !== undefined) {
                                        args.search = query;
                                    }
                                    const users = await new CoreApi(DEFAULT_CONFIG).coreUsersList(
                                        args,
                                    );
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
                                    return this.user?.user.pk === user.pk;
                                }}
                            >
                            </ak-search-select>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal label=${msg("Context")} name="context">
                            <ak-codemirror mode=${CodeMirrorMode.YAML} value=${YAML.stringify({})}>
                            </ak-codemirror>
                        </ak-form-element-horizontal>
                    </div>
                    <div class="pf-c-card__footer">
                        <button
                            class="pf-c-button pf-m-primary"
                            @click=${() => {
                                this.refreshPreview();
                            }}
                        >
                            ${msg("Execute")}
                        </button>
                    </div>
                </div>
                <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__title">${msg("Test results")}</div>
                    ${this.previewLoading
                        ? html`<ak-empty-state loading></ak-empty-state>`
                        : html`<div class="pf-c-card__body pf-c-form pf-m-horizontal">
                              <ak-form-element-horizontal label=${msg("Passing")}>
                                  <div class="pf-c-form__group-label">
                                      <div class="c-form__horizontal-group">
                                          <span class="pf-c-form__label-text">
                                              <ak-status-label
                                                  ?good=${this.preview?.passing}
                                              ></ak-status-label>
                                          </span>
                                      </div>
                                  </div>
                              </ak-form-element-horizontal>
                              <ak-form-element-horizontal label=${msg("Messages")}>
                                  <div class="pf-c-form__group-label">
                                      <div class="c-form__horizontal-group">
                                          <ul>
                                              ${(this.preview?.messages || []).length > 0
                                                  ? this.preview?.messages?.map((m) => {
                                                        return html`<li>
                                                            <span class="pf-c-form__label-text"
                                                                >${m}</span
                                                            >
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
                                  <div class="pf-c-form__group-label">
                                      <div class="c-form__horizontal-group">
                                          <dl class="pf-c-description-list pf-m-horizontal">
                                              <ak-log-viewer
                                                  .logs=${this.preview?.logMessages}
                                              ></ak-log-viewer>
                                          </dl>
                                      </div>
                                  </div>
                              </ak-form-element-horizontal>
                          </div>`}
                </div>
                ${this.previewError
                    ? html`
                          <div class="pf-c-card pf-l-grid__item pf-m-12-col">
                              <div class="pf-c-card__body">${msg("Preview errors")}</div>
                              <div class="pf-c-card__body">
                                  ${this.previewError.map((err) => html`<pre>${err}</pre>`)}
                              </div>
                          </div>
                      `
                    : nothing}
            </div>
        `;
    }

    renderEditForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Executes the Python snippet to determine whether to allow or deny a request.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.executionLogging, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Execution logging")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Policy-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Expression")}
                        ?required=${true}
                        name="expression"
                    >
                        <ak-codemirror
                            mode=${CodeMirrorMode.Python}
                            value="${ifDefined(this.instance?.expression)}"
                            @change=${() => {
                                this._shouldRefresh = true;
                            }}
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Expression using Python.")}
                            <a
                                rel="noopener noreferrer"
                                target="_blank"
                                href="${docLink(
                                    "/docs/customize/policies/expression?utm_source=authentik",
                                )}"
                            >
                                ${msg("See documentation for a list of all variables.")}
                            </a>
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-expression-form": ExpressionPolicyForm;
    }
}
