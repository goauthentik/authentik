import { t } from "@lingui/macro";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import { CoreApi, User } from "authentik-api";
import { me } from "../../api/Users";
import { FlowURLManager } from "../../api/legacy";
import { ifDefined } from "lit-html/directives/if-defined";
import { DEFAULT_CONFIG } from "../../api/Config";
import "../../elements/forms/FormElement";
import "../../elements/EmptyState";
import "../../elements/forms/Form";
import "../../elements/forms/HorizontalFormElement";
import { until } from "lit-html/directives/until";
import { tenant } from "authentik-api/dist/src/api/Config";

@customElement("ak-user-details")
export class UserDetailsPage extends LitElement {

    static get styles(): CSSResult[] {
        return [PFBase, PFCard, PFForm, PFFormControl, PFButton, AKGlobal];
    }

    @property({attribute: false})
    user?: User;

    firstUpdated(): void {
        me().then((user) => {
            this.user = user.user;
        });
    }

    render(): TemplateResult {
        if (!this.user) {
            return html`<ak-empty-state
                ?loading="${true}"
                header=${t`Loading`}>
            </ak-empty-state>`;
        }
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">
                ${t`Update details`}
            </div>
            <div class="pf-c-card__body">
                <ak-form
                    successMessage=${t`Successfully updated details.`}
                    .send=${(data: unknown) => {
                        return new CoreApi(DEFAULT_CONFIG).coreUsersUpdate({
                            id: this.user?.pk || 0,
                            userRequest: data as User
                        });
                    }}>
                    <form class="pf-c-form pf-m-horizontal">
                        <ak-form-element-horizontal
                            label=${t`Username`}
                            ?required=${true}
                            name="username">
                            <input type="text" value="${ifDefined(this.user?.username)}" class="pf-c-form-control" required>
                            <p class="pf-c-form__helper-text">${t`Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.`}</p>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal
                            label=${t`Name`}
                            ?required=${true}
                            name="name">
                            <input type="text" value="${ifDefined(this.user?.name)}" class="pf-c-form-control" required>
                            <p class="pf-c-form__helper-text">${t`User's display name.`}</p>
                        </ak-form-element-horizontal>
                        <ak-form-element-horizontal
                            label=${t`Email`}
                            ?required=${true}
                            name="email">
                            <input type="email" value="${ifDefined(this.user?.email)}" class="pf-c-form-control" required>
                        </ak-form-element-horizontal>

                        <div class="pf-c-form__group pf-m-action">
                            <div class="pf-c-form__horizontal-group">
                                <div class="pf-c-form__actions">
                                    <button class="pf-c-button pf-m-primary">
                                        ${t`Update`}
                                    </button>
                                    ${until(tenant().then(tenant => {
                                        if (tenant.flowUnenrollment) {
                                            return html`<a class="pf-c-button pf-m-danger"
                                                href="/if/flow/${tenant.flowUnenrollment}">
                                                ${t`Delete account`}
                                            </a>`;
                                        }
                                        return html``;
                                    }))}
                                </div>
                            </div>
                        </div>
                    </form>
                </ak-form>
            </div>
        </div>`;
    }

}
