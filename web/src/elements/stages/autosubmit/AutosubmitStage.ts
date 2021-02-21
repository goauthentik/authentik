import { gettext } from "django";
import { CSSResult, customElement, html, property, TemplateResult } from "lit-element";
import { WithUserInfoChallenge } from "../../../api/Flows";
import { COMMON_STYLES } from "../../../common/styles";
import { BaseStage } from "../base";
import "../../Spinner";

export interface AutosubmitChallenge extends WithUserInfoChallenge {
    url: string;
    attrs: { [key: string]: string };
}

@customElement("ak-stage-autosubmit")
export class AutosubmitStage extends BaseStage {

    @property({ attribute: false })
    challenge?: AutosubmitChallenge;

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    updated(): void {
        this.shadowRoot?.querySelectorAll("form").forEach((form) => {form.submit()});
    }

    render(): TemplateResult {
        if (!this.challenge) {
            return html`<ak-loading-state></ak-loading-state>`;
        }
        return html`<header class="pf-c-login__main-header">
                <h1 class="pf-c-title pf-m-3xl">
                    ${this.challenge.title}
                </h1>
            </header>
            <div class="pf-c-login__main-body">
                <form class="pf-c-form" >
                    ${Object.entries(this.challenge.attrs).map(([ key, value ]) => {
                        return html`<input type="hidden" name="${key}" value="${value}">`;
                    })}
                    <ak-spinner></ak-spinner>

                    <div class="pf-c-form__group pf-m-action">
                        <button type="submit" class="pf-c-button pf-m-primary pf-m-block">
                            ${gettext("Continue")}
                        </button>
                    </div>
                </form>
            </div>
            <footer class="pf-c-login__main-footer">
                <ul class="pf-c-login__main-footer-links">
                </ul>
            </footer>`;
    }

}
