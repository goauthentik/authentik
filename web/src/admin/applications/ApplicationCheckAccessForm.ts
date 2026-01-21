import "#components/ak-status-label";
import "#elements/events/LogViewer";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";

import {
    Application,
    CoreApi,
    CoreUsersListRequest,
    PolicyTestResult,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-application-check-access-form")
export class ApplicationCheckAccessForm extends Form<{ forUser: number }> {
    @property({ attribute: false })
    public application!: Application;

    @property({ attribute: false })
    public result: PolicyTestResult | null = null;

    @property({ attribute: false })
    public request?: number;

    getSuccessMessage(): string {
        return msg("Successfully sent test-request.");
    }

    async send(data: { forUser: number }): Promise<PolicyTestResult> {
        this.request = data.forUser;
        const result = await new CoreApi(DEFAULT_CONFIG).coreApplicationsCheckAccessRetrieve({
            slug: this.application?.slug,
            forUser: data.forUser,
        });
        return (this.result = result);
    }

    public override reset(): void {
        super.reset();
        this.result = null;
    }

    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    renderResult(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Passing")}>
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
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <dl class="pf-c-description-list pf-m-horizontal">
                            <ak-log-viewer .logs=${this.result?.logMessages}></ak-log-viewer>
                        </dl>
                    </div>
                </div>
            </ak-form-element-horizontal>
        `;
    }

    renderForm(): TemplateResult {
        return html`<ak-form-element-horizontal label=${msg("User")} required name="forUser">
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
                        return user.pk.toString() === this.request?.toString();
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            ${this.result ? this.renderResult() : nothing}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-check-access-form": ApplicationCheckAccessForm;
    }
}
