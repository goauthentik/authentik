import "#components/ak-status-label";
import "#elements/events/LogViewer";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { PFSize } from "#common/enums";
import { APIMessage, MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import {
    Application,
    CoreApi,
    CoreUsersListRequest,
    PolicyTestResult,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-application-check-access-form")
export class ApplicationCheckAccessForm extends Form<{ forUser: number }> {
    public static override verboseName = msg("Access");
    public static override submitVerb = msg("Check");
    public static override createLabel = msg("Check");
    public static override submittingVerb = msg("Checking");

    static styles: CSSResult[] = [...super.styles, PFDescriptionList];

    #api = new CoreApi(DEFAULT_CONFIG);

    public override size = PFSize.XLarge;

    @property({ attribute: false })
    public application!: Application;

    @property({ attribute: false })
    public result: PolicyTestResult | null = null;

    @property({ attribute: false })
    public request: number | null = null;

    public override formatAPISuccessMessage(): APIMessage {
        return {
            level: MessageLevel.success,
            message: msg("Successfully sent test-request."),
        };
    }

    protected override send(data: { forUser: number }): Promise<PolicyTestResult> {
        this.request = data.forUser;

        return this.#api
            .coreApplicationsCheckAccessRetrieve({
                slug: this.application?.slug,
                forUser: data.forUser,
            })
            .then((result) => {
                this.result = result;
                return result;
            });
    }

    public override reset(): void {
        super.reset();
        this.result = null;
    }

    protected renderResult(): SlottedTemplateResult {
        const { passing, messages = [], logMessages = [] } = this.result || {};

        return html`<ak-form-element-horizontal label=${msg("Passing")}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <span class="pf-c-form__label-text">
                            <ak-status-label ?good=${ifPresent(passing)}></ak-status-label>
                        </span>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Messages")}>
                <div class="pf-c-form__group-label">
                    <div class="c-form__horizontal-group">
                        <ul>
                            ${messages.map((m) => {
                                return html`<li>
                                    <span class="pf-c-form__label-text">${m}</span>
                                </li>`;
                            })}
                        </ul>
                    </div>
                </div>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Log messages")}>
                <ak-log-viewer .items=${logMessages}></ak-log-viewer>
            </ak-form-element-horizontal>`;
    }

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("User")} required name="forUser">
                <ak-search-select
                    placeholder=${msg("Select a user...")}
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };

                        if (query) {
                            args.search = query;
                        }

                        const users = await this.#api.coreUsersList(args);

                        return users.results;
                    }}
                    .renderElement=${(user: User): string => {
                        return user.username;
                    }}
                    .renderDescription=${(user: User): SlottedTemplateResult => {
                        return html`${user.name}`;
                    }}
                    .value=${(user: User | undefined): number | undefined => {
                        return user?.pk;
                    }}
                    .selected=${(user: User): boolean => {
                        return (
                            typeof this.request === "number" &&
                            user.pk.toString() === this.request.toString()
                        );
                    }}
                >
                </ak-search-select>
            </ak-form-element-horizontal>
            ${this.renderResult()}`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-check-access-form": ApplicationCheckAccessForm;
    }
}
