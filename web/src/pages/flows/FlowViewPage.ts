import { t } from "@lingui/macro";
import {
    css,
    CSSResult,
    customElement,
    html,
    LitElement,
    property,
    TemplateResult,
} from "lit-element";

import "../../elements/Tabs";
import "../../elements/PageHeader";
import "../../elements/events/ObjectChangelog";
import "../../elements/buttons/SpinnerButton";
import "../policies/BoundPoliciesList";
import "./BoundStagesList";
import "./FlowDiagram";
import { Flow, FlowsApi } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "../../api/Config";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import AKGlobal from "../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";

@customElement("ak-flow-view")
export class FlowViewPage extends LitElement {
    @property()
    set flowSlug(value: string) {
        new FlowsApi(DEFAULT_CONFIG)
            .flowsInstancesRetrieve({
                slug: value,
            })
            .then((flow) => {
                this.flow = flow;
            });
    }

    @property({ attribute: false })
    flow!: Flow;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFDescriptionList,
            PFButton,
            PFCard,
            PFContent,
            PFGrid,
            AKGlobal,
        ].concat(
            css`
                img.pf-icon {
                    max-height: 24px;
                }
                ak-tabs {
                    height: 100%;
                }
            `,
        );
    }

    render(): TemplateResult {
        if (!this.flow) {
            return html``;
        }
        return html`<ak-page-header
                icon="pf-icon pf-icon-process-automation"
                header=${this.flow.name}
                description=${this.flow.title}
            >
            </ak-page-header>
            <ak-tabs>
                <div
                    slot="page-overview"
                    data-tab-title="${t`Flow Overview`}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-l-grid pf-m-gutter">
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-2-col-on-xl pf-m-2-col-on-2xl"
                        >
                            <div class="pf-c-card__title">${t`Related`}</div>
                            <div class="pf-c-card__body">
                                <dl class="pf-c-description-list">
                                    <div class="pf-c-description-list__group">
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${t`Execute flow`}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <button
                                                    class="pf-c-button pf-m-primary"
                                                    @click=${() => {
                                                        new FlowsApi(DEFAULT_CONFIG)
                                                            .flowsInstancesExecuteRetrieve({
                                                                slug: this.flow.slug,
                                                            })
                                                            .then((link) => {
                                                                const finalURL = `${link.link}?next=/%23${window.location.hash}`;
                                                                window.open(finalURL, "_blank");
                                                            });
                                                    }}
                                                >
                                                    ${t`Execute`}
                                                </button>
                                            </div>
                                        </dd>
                                        <dt class="pf-c-description-list__term">
                                            <span class="pf-c-description-list__text"
                                                >${t`Export flow`}</span
                                            >
                                        </dt>
                                        <dd class="pf-c-description-list__description">
                                            <div class="pf-c-description-list__text">
                                                <a
                                                    class="pf-c-button pf-m-secondary"
                                                    href=${this.flow.exportUrl}
                                                >
                                                    ${t`Export`}
                                                </a>
                                            </div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                        </div>
                        <div
                            class="pf-c-card pf-l-grid__item pf-m-12-col pf-m-10-col-on-xl pf-m-10-col-on-2xl"
                        >
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">
                                    <ak-flow-diagram flowSlug=${this.flow.slug}> </ak-flow-diagram>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div
                    slot="page-stage-bindings"
                    data-tab-title="${t`Stage Bindings`}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-bound-stages-list .target=${this.flow.pk}> </ak-bound-stages-list>
                        </div>
                    </div>
                </div>
                <div
                    slot="page-policy-bindings"
                    data-tab-title="${t`Policy / Group / User Bindings`}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__title">
                            ${t`These bindings control which users can access this flow.`}
                        </div>
                        <div class="pf-c-card__body">
                            <ak-bound-policies-list .target=${this.flow.policybindingmodelPtrId}>
                            </ak-bound-policies-list>
                        </div>
                    </div>
                </div>
                <div
                    slot="page-changelog"
                    data-tab-title="${t`Changelog`}"
                    class="pf-c-page__main-section pf-m-no-padding-mobile"
                >
                    <div class="pf-c-card">
                        <div class="pf-c-card__body">
                            <ak-object-changelog
                                targetModelPk=${this.flow.pk || ""}
                                targetModelApp="authentik_flows"
                                targetModelName="flow"
                            >
                            </ak-object-changelog>
                        </div>
                    </div>
                </div>
            </ak-tabs>`;
    }
}
