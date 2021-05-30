import "./locale";
import "../elements/messages/MessageContainer";
import { css, CSSResult, customElement, html, LitElement, property, TemplateResult } from "lit-element";

import Carbon from "carbon-components/css/carbon-components.min.css";
import "carbon-web-components/es/components/ui-shell/header";
import "carbon-web-components/es/components/ui-shell/header-name";
import "carbon-web-components/es/components/ui-shell/header-nav";
import "carbon-web-components/es/components/ui-shell/header-nav-item";
import { CurrentTenant } from "authentik-api";
import { DefaultTenant } from "../elements/sidebar/SidebarBrand";
import { tenant } from "../api/Config";
import { configureSentry } from "../api/Sentry";

@customElement("ak-interface-user")
export class UserInterface extends LitElement {

    @property({ attribute: false })
    tenant: CurrentTenant = DefaultTenant;

    static get styles(): CSSResult[] {
        return [Carbon, css`
            bx-header img {
                max-height: 100%;
                padding: 0 2px;
            }
        `];
    }

    firstUpdated(): void {
        configureSentry(true);
        tenant().then(tenant => this.tenant = tenant);
    }

    render(): TemplateResult {
        return html`<div id="root">
            <div id="root-inner">
                <div id="main-content" name="main-content" class="bx--body" role="none">
                    <bx-header aria-label="IBM Platform Name" role="banner">
                        <img src="${this.tenant.brandingLogo}" alt="authentik icon" loading="lazy" />
                        <bx-header-nav menu-bar-label="IBM [Platform]" role="navigation">
                            <bx-header-nav-item href="javascript:void 0">Link 1</bx-header-nav-item>
                            <bx-header-nav-item href="javascript:void 0">Link 2</bx-header-nav-item>
                            <bx-header-nav-item href="javascript:void 0">Link 3</bx-header-nav-item>
                        </bx-header-nav>
                    </bx-header>
                    <main class="bx--content">
                        <div class="bx--grid">
                            <div class="bx--row">
                                <div class="bx--offset-lg-2 bx--col-lg-8">
                                    <h2>
                                        Purpose and function
                                    </h2>
                                    <p>
                                        The shell is perhaps the most crucial piece of any UI built with Carbon. It contains the
                                        shared navigation framework
                                        for the entire design system and ties the products in IBM’s portfolio together in a
                                        cohesive and elegant way. The
                                        shell is the home of the topmost navigation, where users can quickly and dependably gain
                                        their bearings and move
                                        between pages.
                                        <br>
                                        <br>
                                        The shell was designed with maximum flexibility built in, to serve the needs of a broad
                                        range of products and users.
                                        Adopting the shell ensures compliance with IBM design standards, simplifies development
                                        efforts, and provides great
                                        user experiences. All IBM products built with Carbon are required to use the shell’s
                                        header.
                                        <br>
                                        <br>
                                        To better understand the purpose and function of the UI shell, consider the “shell” of
                                        MacOS, which contains the Apple
                                        menu, top-level navigation, and universal, OS-level controls at the top of the screen,
                                        as well as a universal dock
                                        along the bottom or side of the screen. The Carbon UI shell is roughly analogous in
                                        function to these parts of the Mac
                                        UI. For example, the app switcher portion of the shell can be compared to the dock in
                                        MacOS.
                                    </p>
                                    <h2>
                                        Header responsive behavior
                                    </h2>
                                    <p>
                                        As a header scales down to fit smaller screen sizes, headers with persistent side nav
                                        menus should have the side nav
                                        collapse into “hamburger” menu. See the example to better understand responsive behavior
                                        of the header.
                                    </p>
                                    <h2>
                                        Secondary navigation
                                    </h2>
                                    <p>
                                        The side-nav contains secondary navigation and fits below the header. It can be
                                        configured to be either fixed-width or
                                        flexible, with only one level of nested items allowed. Both links and category lists can
                                        be used in the side-nav and
                                        may be mixed together. There are several configurations of the side-nav, but only one
                                        configuration should be used per
                                        product section. If tabs are needed on a page when using a side-nav, then the tabs are
                                        secondary in hierarchy to the
                                        side-nav.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </main>


                </div>
                <!---->
            </div>
        </div>`;
    }

}
