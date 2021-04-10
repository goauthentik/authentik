import { t } from "@lingui/macro";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";

import "../../elements/Tabs";
import "../../elements/PageHeader";
import "../../elements/events/ObjectChangelog";
import "../../elements/buttons/SpinnerButton";
import "../policies/BoundPoliciesList";
import "./BoundStagesList";
import "./FlowDiagram";
import { Flow, FlowsApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import AKGlobal from "../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";

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
        return [PFBase, PFPage, PFButton, PFCard, PFContent, PFGallery, AKGlobal].concat(
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
        return html`<ak-page-header
            icon="pf-icon pf-icon-process-automation"
            header=${this.flow.name}
            description=${this.flow.title}>
            </ak-page-header>
            <ak-tabs>
                <div slot="page-1" data-tab-title="${t`Flow Overview`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-l-gallery pf-m-gutter">
                        <div class="pf-c-card pf-l-gallery__item" style="grid-column-end: span 4;grid-row-end: span 2;">
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">
                                    <ak-flow-diagram flowSlug=${this.flow.slug}>
                                    </ak-flow-diagram>
                                </div>
                            </div>
                        </div>
                        <div class="pf-c-card pf-l-gallery__item">
                            <div class="pf-c-card__title">${t`Related`}</div>
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list">
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text">${t`Execute flow`}</span>
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <button
                                                    class="pf-c-button pf-m-secondary"
                                                    @click=${() => {
                                                    new FlowsApi(DEFAULT_CONFIG).flowsInstancesExecute({
                                                        slug: this.flow.slug
                                                    }).then(link => {
                                                        const finalURL = `${link.link}?next=/%23${window.location.href}`;
                                                        window.open(finalURL, "_blank");
                                                    });
                                                }}>
                                                    ${t`Execute`}
                                                </button>
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                        </div>
                    </div>
                </div>
                <div slot="page-2" data-tab-title="${t`Stage Bindings`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-bound-stages-list .target=${this.flow.pk}>
                            </ak-bound-stages-list>
                        </div>
                    </div>
                </div>
                <div slot="page-3" data-tab-title="${t`Policy Bindings`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                    <div class="pf-c-card">
                        <div class="pf-c-card__title">${t`These policies control which users can access this flow.`}</div>
                        <div class="pf-c-card__body">
                            <ak-bound-policies-list .target=${this.flow.policybindingmodelPtrId}>
                            </ak-bound-policies-list>
                        </div>
                    </div>
                </div>
                <div slot="page-4" data-tab-title="${t`Changelog`}" class="pf-c-page__main-section pf-m-no-padding-mobile">
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
