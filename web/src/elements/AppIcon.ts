import { PFSize } from "#common/enums";

import Styles from "#elements/AppIcon.css";
import { AKElement } from "#elements/Base";
import { FontAwesomeProtocol } from "#elements/utils/images";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

export interface IAppIcon {
    name?: string | null;
    icon?: string | null;
    size?: PFSize | null;
}

@customElement("ak-app-icon")
export class AppIcon extends AKElement implements IAppIcon {
    public static readonly FontAwesomeProtocol = FontAwesomeProtocol;

    static styles: CSSResult[] = [Styles];

    // Render to light DOM so Font Awesome fonts (loaded globally) work correctly.
    // This avoids the issue where @font-face rules with relative paths in PatternFly's
    // FA icons CSS don't resolve correctly in Shadow DOM.
    protected override createRenderRoot() {
        return this;
    }

    @property({ type: String })
    public name: string | null = null;

    @property({ type: String })
    public icon: string | null = null;

    @property({ reflect: true })
    public size: PFSize = PFSize.Medium;

    override render(): TemplateResult {
        const applicationName = this.name ?? msg("Application");
        const label = msg(str`${applicationName} Icon`);

        // Check for Font Awesome icons (fa://fa-icon-name)
        if (this.icon?.startsWith(AppIcon.FontAwesomeProtocol)) {
            const iconClass = this.icon.slice(AppIcon.FontAwesomeProtocol.length);
            return html`<i
                part="icon font-awesome"
                role="img"
                aria-label=${label}
                class="icon fas ${iconClass}"
            ></i>`;
        }

        const insignia = this.name?.charAt(0).toUpperCase() ?? "�";

        // Check for image URLs (http://, https://, or file paths)
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

        // Fallback to first letter insignia
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
