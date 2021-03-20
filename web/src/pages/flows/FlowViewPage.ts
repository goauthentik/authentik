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
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";

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
        return [PFBase, PFPage, PFCard, PFContent, PFFlex, PFSizing, PFDisplay, AKGlobal].concat(
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
                    <div class="pf-u-display-flex">
                        <div class="pf-u-w-75">
                            <div class="pf-c-card">
                                <div class="pf-c-card__body">
                                    <ak-flow-diagram flowSlug=${this.flow.slug}>
                                    </ak-flow-diagram>
                                </div>
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
