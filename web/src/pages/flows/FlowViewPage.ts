import { gettext } from "django";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";

import "../../elements/Tabs";
import "../../elements/events/ObjectChangelog";
import "../../elements/buttons/ModalButton";
import "../../elements/buttons/SpinnerButton";
import "../../elements/policies/BoundPoliciesList";
import "./BoundStagesList";
import "./FlowDiagram";
import { Flow, FlowsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import AKGlobal from "../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import { AdminURLManager } from "../../api/legacy";

@customElement("ak-flow-view")
export class FlowViewPage extends LitElement {
    @property()
    set flowSlug(value: string) {
        new FlowsApi(DEFAULT_CONFIG).flowsInstancesRead({
            slug: value
        }).then((flow) => {
            this.flow = flow;
        });
    }

    @property({attribute: false})
    flow!: Flow;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFCard, PFContent, PFGallery, AKGlobal].concat(
            css`
                img.pf-icon {
                    max-height: 24px;
                }
                ak-tabs {
                    height: 100%;
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
                <div slot="page-1" data-tab-title="${gettext("Flow Overview")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-l-gallery pf-m-gutter">
                        <div class="pf-c-card pf-l-gallery__item" style="grid-column-end: span 3;grid-row-end: span 2;">
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">
                                    <ak-flow-diagram flowSlug=${this.flow.slug}>
                                    </ak-flow-diagram>
                                </div>
                            </div>
                        </div>
                        <div class="pf-c-card pf-l-gallery__item">
                            <div class="pf-c-card__title">${gettext("Related")}</div>
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list">
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${gettext("Execute flow")}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <a class="pf-c-button pf-m-secondary ak-root-link" href="${AdminURLManager.flows(`${this.flow.pk}/execute/?next=/%23${window.location.href}`)}">
                                                    ${gettext("Execute")}
                                                </a>
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
                <div slot="page-2" data-tab-title="${gettext("Stage Bindings")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-bound-stages-list .target=${this.flow.pk}>
                            </ak-bound-stages-list>
                        </div>
                    </div>
                </div>
                <div slot="page-3" data-tab-title="${gettext("Policy Bindings")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__title">${gettext("These policies control which users can access this flow.")}</div>
                        <div class="pf-c-card__body">
                            <ak-bound-policies-list .target=${this.flow.policybindingmodelPtrId}>
                            </ak-bound-policies-list>
                        </div>
                    </div>
                </div>
                <div slot="page-4" data-tab-title="${gettext("Changelog")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.flow.pk || ""}
                                targetModelApp="authentik_flows"
                                targetModelName="flow">
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
            </ak-tabs>`;
    }
}
