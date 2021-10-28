import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators";
import { ifDefined } from "lit/directives/if-defined";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";

@customElement("ak-form-static")
export class FormStatic extends LitElement {
    @property()
    userAvatar?: string;

    @property()
    user = "";

    static get styles(): CSSResult[] {
        return [
            PFAvatar,
            css`
                /* Form with user */
                .form-control-static {
                    margin-top: var(--pf-global--spacer--sm);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }
                .form-control-static .avatar {
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
            `,
        ];
    }

    render(): TemplateResult {
        return html`
            <div class="form-control-static">
                <div class="avatar">
                    <img
                        class="pf-c-avatar"
                        src="${ifDefined(this.userAvatar)}"
                        alt="${t`User's avatar`}"
                    />
                    ${this.user}
                </div>
                <slot name="link"></slot>
            </div>
        `;
    }
}
