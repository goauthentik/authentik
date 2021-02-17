import { CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../common/styles";
import { SpinnerSize } from "../Spinner";

@customElement("ak-loading-state")
export class LoadingState extends LitElement {

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
    }

    render(): TemplateResult {
        return html`<div class="pf-c-empty-state pf-m-full-height">
            <div class="pf-c-empty-state__content">
                <div class="pf-l-bullseye">
                    <div class="pf-l-bullseye__item">
                        <ak-spinner size="${SpinnerSize.XLarge}"></ak-spinner>
                    </div>
                </div>
            </div>
        </div>`;
    }
}
