import { customElement, CSSResult, html, LitElement, property, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFFlex from "@patternfly/patternfly/layouts/Flex/flex.css";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import AKGlobal from "../authentik.css";

@customElement("ak-banner")
export class Banner extends LitElement {

    @property()
    level = "pf-m-warning";

    static get styles(): CSSResult[] {
        return [PFBase, PFBanner, PFFlex, AKGlobal];
    }

    render(): TemplateResult {
        return html`<div class="pf-c-banner ${this.level} pf-m-sticky">
            <div class="pf-l-flex pf-m-justify-content-center pf-m-justify-content-space-between-on-lg pf-m-nowrap" style="height: 100%;">
                <div class="pf-u-display-none pf-u-display-block-on-lg">
                    <slot></slot>
                </div>
            </div>
        </div>`;
    }

}
