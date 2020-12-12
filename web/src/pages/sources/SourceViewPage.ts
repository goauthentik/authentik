import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../../common/styles";

import "../../elements/Tabs";
import "../../elements/AdminLoginsChart";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/policies/BoundPoliciesList";
import { Source } from "../../api/source";

@customElement("ak-source-view")
export class SourceViewPage extends LitElement {
    @property()
    set args(value: { [key: string]: string }) {
        this.sourceSlug = value.slug;
    }

    @property()
    set sourceSlug(value: string) {
        Source.get(value).then((source) => (this.source = source));
    }

    @property({attribute: false})
    source?: Source;

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
        if (!this.source) {
            return html``;
        }
        return html`<section class="pf-c-page__main-section pf-m-light">
                <div class="pf-c-content">
                    <h1>
                        <i class="pf-icon pf-icon-middleware"></i>
                        ${this.source?.name}
                    </h1>
                </div>
            </section>
            <ak-tabs>
                <div slot="page-2" data-tab-title="Policy Bindings" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__header">
                            <div class="pf-c-card__header-main">
                                ${gettext("These policies control which users can access this application.")}
                            </div>
                        </div>
                        <ak-bound-policies-list .target=${this.source.pk}>
                        </ak-bound-policies-list>
                    </div>
                </div>
            </ak-tabs>`;
    }
}
