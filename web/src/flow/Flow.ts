import "#flow/FlowExecutor";
import "#flow/inspector/FlowInspector";
import "#flow/components/ak-brand-footer";

import { light } from "#elements/directives/light";
import { Interface } from "#elements/Interface";

import AKPlaceholder from "#styles/authentik/base/placeholder.css";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFLogin from "@patternfly/patternfly/components/Login/login.css";
import PFSpinner from "@patternfly/patternfly/components/Spinner/spinner.css";

@customElement("ak-flow")
export class Flow extends Interface {
    static readonly styles = [PFDrawer, PFLogin, PFSpinner, AKPlaceholder];

    @property()
    public slug?: string;

    @property()
    public layout?: string = "stacked";

    protected renderPlacehonder() {
        return html`<div class="ak-c-placeholder" id="ak-placeholder" slot="placeholder">
            <span class="pf-c-spinner" role="progressbar" aria-valuetext=${msg("Loading...")}>
                <span class="pf-c-spinner__clipper"></span>
                <span class="pf-c-spinner__lead-ball"></span>
                <span class="pf-c-spinner__tail-ball"></span>
            </span>
        </div>`;
    }

    render() {
        const { slug, layout } = this;
        const footerClasses = classMap({
            "pf-c-login_footer": true,
            "pf-m-dark": this.layout === FlowLayoutEnum.Stacked,
        });

        return html`
            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer pf-m-collapsed" id="flow-drawer">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                ${light(
                                    html`<ak-flow-executor
                                        slug="${slug}"
                                        class="pf-c-login"
                                        data-layout="${layout}"
                                        loading
                                    >
                                        ${this.renderPlaceholder()}
                                    </ak-flow-executor>`
                                )}
                                <footer
                                    aria-label=${msg("Site footer")}
                                    name="site-footer"
                                    part="footer"
                                    class=${footerClasses}
                                >
                                    <ak-brand-links name="flow-links"></ak-brand-links>
                                </footer>
                            </div>
                        </div>

                        <ak-flow-inspector
                            id="flow-inspector"
                            data-registration="lazy"
                            class="pf-c-drawer__panel pf-m-width-33"
                            slug=${slug}
                        ></ak-flow-inspector>
                    </div>
                </div>
            </div>
        `;
    }
}
