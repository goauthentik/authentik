import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import AKGlobal from "../../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import { CoreApi, User } from "authentik-api";
import { me } from "../../api/Users";
import "../../elements/forms/FormElement";
import "../../elements/EmptyState";
import { FlowURLManager } from "../../api/legacy";
import "@polymer/paper-input/paper-input";
import "@polymer/iron-form/iron-form";
import { DEFAULT_CONFIG } from "../../api/Config";
import { PaperInputElement } from "@polymer/paper-input/paper-input";
import { showMessage } from "../../elements/messages/MessageContainer";

export interface ErrorResponse {
    [key: string]: string[];
}

@customElement("ak-form")
export class Form extends LitElement {

    @property()
    successMessage = "";

    @property()
    send!: (data: Record<string, unknown>) => Promise<unknown>;

    submit(ev: Event): void {
        ev.preventDefault();
        const ironForm = this.shadowRoot?.querySelector("iron-form");
        if (!ironForm) {
            return;
        }
        const data = ironForm.serializeForm();
        this.send(data).then(() => {
            showMessage({
                level_tag: "success",
                message: this.successMessage
            });
        }).catch((ex: Response) => {
            if (ex.status > 399 && ex.status < 500) {
                return ex.json();
            }
            return ex;
        }).then((errorMessage?: ErrorResponse) => {
            if (!errorMessage) return;
            const elements: PaperInputElement[] = ironForm._getSubmittableElements();
            elements.forEach((element) => {
                const elementName = element.name;
                if (!elementName) return;
                if (elementName in errorMessage) {
                    element.errorMessage = errorMessage[elementName].join(", ");
                    element.invalid = true;
                }
            });
        });
    }

    render(): TemplateResult {
        return html`<iron-form
            @iron-form-presubmit=${(ev: Event) => { this.submit(ev); }}>
            <slot></slot>
        </iron-form>`;
    }

}

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
                header=${gettext("Loading")}>
            </ak-empty-state>`;
        }
        return html`<div class="pf-c-card">
            <div class="pf-c-card__title">
                ${gettext("Update details")}
            </div>
            <div class="pf-c-card__body">
                <ak-form
                    successMessage=${gettext("Successfully updated details.")}
                    .send=${(data: unknown) => {
                        return new CoreApi(DEFAULT_CONFIG).coreUsersUpdate({
                            id: this.user?.pk || 0,
                            data: data as User
                        });
                    }}>
                    <form class="pf-c-form pf-m-horizontal">
                        <paper-input
                            name="username"
                            ?alwaysFloatLabel=${true}
                            label="${gettext("Username")}"
                            value=${this.user.username}>
                        </paper-input>
                        <p class="pf-c-form__helper-text">${gettext("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.")}</p>
                        <paper-input
                            name="name"
                            ?alwaysFloatLabel=${true}
                            label="${gettext("Name")}"
                            value=${this.user.name}>
                        </paper-input>
                        <p class="pf-c-form__helper-text">${gettext("User's display name.")}</p>
                        <paper-input
                            name="email"
                            ?alwaysFloatLabel=${true}
                            type="email"
                            label="${gettext("Email address")}"
                            value=${this.user.email || ""}>
                        </paper-input>

                        <div class="pf-c-form__group pf-m-action">
                            <div class="pf-c-form__horizontal-group">
                                <div class="pf-c-form__actions">
                                    <button class="pf-c-button pf-m-primary">
                                        ${gettext("Update")}
                                    </button>
                                    <a class="pf-c-button pf-m-danger"
                                        href="${FlowURLManager.defaultUnenrollment()}">
                                        ${gettext("Delete account")}
                                    </a>
                                </div>
                            </div>
                        </div>
                    </form>
                </ak-form>
            </div>
        </div>`;
    }

}
