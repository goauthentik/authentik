import { PFSize } from "#common/enums";

import Styles from "#elements/AppIcon.css";
import { AKElement } from "#elements/Base";
import { FontAwesomeProtocol } from "#elements/utils/images";

import { msg, str } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFFAIcons from "@patternfly/patternfly/base/patternfly-fa-icons.css";

export interface IAppIcon {
    name?: string | null;
    icon?: string | null;
    iconThemedUrls?: Record<string, string> | null;
    size?: PFSize | null;
}

@customElement("ak-app-icon")
export class AppIcon extends AKElement implements IAppIcon {
    public static readonly FontAwesomeProtocol = FontAwesomeProtocol;

    static styles: CSSResult[] = [PFFAIcons, Styles];

    @property({ type: String })
    public name: string | null = null;

    @property({ type: String })
    public icon: string | null = null;

    @property({ type: Object })
    public iconThemedUrls: Record<string, string> | null = null;

    @property({ reflect: true })
    public size: PFSize = PFSize.Medium;

    #wrap(icon: TemplateResult): TemplateResult {
        // PatternFly's font awesome rules use descendant selectors (`* .fa-*`),
        // so the icon needs at least one ancestor inside the shadow DOM to pick up those styles.
        return html`<span class="icon-wrapper">${icon}</span>`;
    }

    override render(): TemplateResult {
        const applicationName = this.name ?? msg("Application");
        const label = msg(str`${applicationName} Icon`);

        // Check for Font Awesome icons (fa://fa-icon-name)
        if (this.icon?.startsWith(AppIcon.FontAwesomeProtocol)) {
            const iconClass = this.icon.slice(AppIcon.FontAwesomeProtocol.length);
            return this.#wrap(
                html`<i
                    part="icon font-awesome"
                    role="img"
                    aria-label=${label}
                    class="icon fas ${iconClass}"
                ></i>`,
            );
        }

        const insignia = this.name?.charAt(0).toUpperCase() ?? "�";

        // Check for image URLs (http://, https://, or file paths)
        // Use themed URL if available, otherwise fall back to icon
        const resolvedIcon = this.iconThemedUrls?.[this.activeTheme] ?? this.icon;
        if (resolvedIcon) {
            return this.#wrap(
                html`<img
                    part="icon image"
                    role="img"
                    aria-label=${label}
                    class="icon"
                    src=${resolvedIcon}
                    alt=${insignia}
                />`,
            );
        }

        // Fallback to first letter insignia
        return this.#wrap(
            html`<span part="icon insignia" role="img" aria-label=${label} class="icon"
                >${insignia}</span
            >`,
        );
    }
}

export default AppIcon;

declare global {
    interface HTMLElementTagNameMap {
        "ak-app-icon": AppIcon;
    }
}
