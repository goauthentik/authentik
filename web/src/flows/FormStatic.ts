import { css, CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";

@customElement("ak-form-static")
export class FormStatic extends LitElement {

    static get styles(): CSSResult[] {
        return [css`
            /* Form with user */
            .form-control-static {
                margin-top: var(--pf-global--spacer--sm);
                display: flex;
                align-items: center;
                justify-content: space-between;
            }
            .form-control-static slot[name=avatar] {
                display: flex;
                align-items: center;
            }
            .form-control-static img {
                margin-right: var(--pf-global--spacer--xs);
            }
            .form-control-static a {
                padding-top: var(--pf-global--spacer--xs);
                padding-bottom: var(--pf-global--spacer--xs);
                line-height: var(--pf-global--spacer--xl);
            }
        `];
    }

    render(): TemplateResult {
        return html`
            <div class="form-control-static">
                <slot name="avatar"></slot>
                <slot name="link"></slot>
            </div>
        `;
    }

}
