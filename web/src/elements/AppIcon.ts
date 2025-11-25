import { PFSize } from "#common/enums";

import Styles from "#elements/AppIcon.css";
import { AKElement } from "#elements/Base";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFFAIcons from "@patternfly/patternfly/base/patternfly-fa-icons.css";

export interface IAppIcon {
    name?: string | null;
    icon?: string | null;
    size?: PFSize | null;
}

@customElement("ak-app-icon")
export class AppIcon extends AKElement implements IAppIcon {
    public static readonly FontAwesomeProtocol = "fa://";

    static styles: CSSResult[] = [PFFAIcons, Styles];

    @property({ type: String })
    public name: string | null = null;

    @property({ type: String })
    public icon: string | null = null;

    @property({ reflect: true })
    public size: PFSize = PFSize.Medium;

    render(): TemplateResult {
        const applicationName = this.name ?? msg("Application");
        const label = msg(str`${applicationName} Icon`);

        if (this.icon?.startsWith(AppIcon.FontAwesomeProtocol)) {
            return html`<i
                part="icon font-awesome"
                role="img"
                aria-label=${label}
                class="icon fas ${this.icon.slice(AppIcon.FontAwesomeProtocol.length)}"
            ></i>`;
        }

        const insignia = this.name?.charAt(0).toUpperCase() ?? "�";

        if (this.icon) {
            return html`<img
                part="icon image"
                role="img"
                aria-label=${label}
                class="icon"
                src=${this.icon}
                alt=${insignia}
            />`;
        }

        return html`<span part="icon insignia" role="img" aria-label=${label} class="icon"
            >${insignia}</span
        >`;
    }
}

export default AppIcon;

declare global {
    interface HTMLElementTagNameMap {
        "ak-app-icon": AppIcon;
    }
}
