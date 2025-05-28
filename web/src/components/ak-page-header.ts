import "#components/ak-nav-buttons";
import { AKPageNavbar } from "#components/ak-page-navbar";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { CSSResult, LitElement, css } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface PageHeaderInit {
    header?: string;
    description?: string;
    icon?: string;
    iconImage?: boolean;
}

//#region Events

export interface SidebarToggleEventDetail {
    open?: boolean;
}

//#endregion

//#region Page Header

/**
 * A page header component, used to display the page title and description.
 *
 * Internally, this component dispatches the `ak-page-header` event, which is
 * listened to by the `ak-page-navbar` component.
 *
 * @singleton
 */
@customElement("ak-page-header")
export class AKPageHeader extends LitElement implements PageHeaderInit {
    @property({ type: String })
    header?: string;

    @property({ type: String })
    description?: string;

    @property({ type: String })
    icon?: string;

    @property({ type: Boolean })
    iconImage = false;

    static get styles(): CSSResult[] {
        return [
            css`
                :host {
                    display: none;
                }
            `,
        ];
    }

    connectedCallback(): void {
        super.connectedCallback();

        AKPageNavbar.setNavbarDetails({
            header: this.header,
            description: this.description,
            icon: this.icon,
            iconImage: this.iconImage,
        });
    }

    updated(): void {
        AKPageNavbar.setNavbarDetails({
            header: this.header,
            description: this.description,
            icon: this.icon,
            iconImage: this.iconImage,
        });
    }
}

//#endregion

declare global {
    interface HTMLElementTagNameMap {
        "ak-page-header": AKPageHeader;
    }
}
