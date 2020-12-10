import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../common/styles";
import { Flow } from "../../api/flow";

import "../../elements/Tabs";
import "../../elements/AdminLoginsChart";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/policies/BoundPoliciesList";
import "./BoundStagesList";

@customElement("ak-flow-view")
export class FlowViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.flowSlug = value.slug;
    }

    @property()
    set flowSlug(value: string) {
        Flow.get(value).then((flow) => (this.flow = flow));
    }

    @property({attribute: false})
    flow?: Flow;

    static get styles(): CSSResult[] {
        return COMMON_STYLES.concat(
            css`
                img.pf-icon {
                    max-height: 24px;
                }
            `
        );
    }

    render(): TemplateResult {
        if (!this.flow) {
            return html``;
        }
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <i class="pf-icon pf-icon-process-automation"></i>
                        ${this.flow?.name}
                    </h1>
                    <p>${this.flow?.title}</p>
                </div>
            </section>
            <ak-tabs>
                <div slot="page-2" data-tab-title="${gettext("Stage Bindings")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__header">
                            <div class="pf-c-card__header-main">
                                ${gettext("These policies control which users can access this flow.")}
                            </div>
                        </div>
                        <ak-bound-stages-list .target=${this.flow.pk}>
                        </ak-bound-stages-list>
                    </div>
                </div>
                <div slot="page-3" data-tab-title="${gettext("Policy Bindings")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__header">
                            <div class="pf-c-card__header-main">
                                ${gettext("These policies control which users can access this flow.")}
                            </div>
                        </div>
                        <ak-bound-policies-list .target=${this.flow.policybindingmodel_ptr_id}>
                        </ak-bound-policies-list>
                    </div>
                </div>
            </ak-tabs>`;
    }
}
