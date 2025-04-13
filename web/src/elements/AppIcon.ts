import { PFSize } from "@goauthentik/common/enums.js";
import { AKElement } from "@goauthentik/elements/Base";
import { P, match } from "ts-pattern";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFFAIcons from "@patternfly/patternfly/base/patternfly-fa-icons.css";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";

export interface IAppIcon {
    name?: string;
    icon?: string;
    size?: PFSize;
}

@customElement("ak-app-icon")
export class AppIcon extends AKElement implements IAppIcon {
    @property({ type: String })
    name?: string;

    @property({ type: String })
    icon?: string;

    @property({ reflect: true })
    size: PFSize = PFSize.Medium;

    static get styles(): CSSResult[] {
        return [
            PFFAIcons,
            PFAvatar,
            css`
                :host {
                    max-height: calc(var(--icon-height) + var(--icon-border) + var(--icon-border));
                }
                :host([size="pf-m-lg"]) {
                    --icon-height: 4rem;
                    --icon-border: 0.25rem;
                }
                :host([size="pf-m-md"]) {
                    --icon-height: 2rem;
                    --icon-border: 0.125rem;
                }
                :host([size="pf-m-sm"]) {
                    --icon-height: 1rem;
                    --icon-border: 0.125rem;
                }
                :host([size="pf-m-xl"]) {
                    --icon-height: 6rem;
                    --icon-border: 0.25rem;
                }
                .pf-c-avatar {
                    --pf-c-avatar--BorderRadius: 0;
                    --pf-c-avatar--Height: calc(
                        var(--icon-height) + var(--icon-border) + var(--icon-border)
                    );
                    --pf-c-avatar--Width: calc(
                        var(--icon-height) + var(--icon-border) + var(--icon-border)
                    );
                }
                .icon {
                    font-size: var(--icon-height);
                    color: var(--ak-global--Color--100);
                    padding: var(--icon-border);
                    max-height: calc(var(--icon-height) + var(--icon-border) + var(--icon-border));
                    line-height: calc(var(--icon-height) + var(--icon-border) + var(--icon-border));
                    filter: drop-shadow(5px 5px 5px rgba(128, 128, 128, 0.25));
                }
                div {
                    height: calc(var(--icon-height) + var(--icon-border) + var(--icon-border));
                }
            `,
        ];
    }

    // Validate if icon URL might be valid
    isValidIcon(icon: string): boolean {
        if (!icon) return false;
        if (icon.startsWith("fa://")) return true;

        try {
            // Simple check for URL format
            new URL(icon);
            return true;
        } catch {
            return false;
        }
    }

    // Render fallback icon when no valid icon or name is available
    renderFallbackIcon(): TemplateResult {
        return html`<div><i class="icon fas fa-question-circle"></i></div>`;
    }

    // Render icon based on first letter of name
    renderLetterIcon(name: string): TemplateResult {
        if (!name || name.length === 0) {
            return this.renderFallbackIcon();
        }
        return html`<span class="icon">${name.charAt(0).toUpperCase()}</span>`;
    }

    render(): TemplateResult {
        // prettier-ignore
        return match([this.name, this.icon])
            .with([undefined, undefined], () => this.renderFallbackIcon())
            .with([P._, P.string.startsWith("fa://")],
                ([_name, icon]) => html`<div><i class="icon fas ${icon.replaceAll("fa://", "")}"></i></div>`)
            .with([P._, P.string],
                ([name, icon]) => {
                    if (!this.isValidIcon(icon)) {
                        // If icon is not valid, fall back to letter or question mark
                        return name ? this.renderLetterIcon(name) : this.renderFallbackIcon();
                    }
                    
                    return html`<img 
                        class="icon pf-c-avatar" 
                        src="${icon}" 
                        alt="${msg("Application Icon")}" 
                        @error=${(e: Event) => {
                            const img = e.target as HTMLImageElement;
                            img.style.display = 'none';
                            const div = img.parentElement;
                            if (div) {
                                // If image fails to load, try to display first letter or fallback
                                const fallback = name ? 
                                    `<span class="icon">${name.charAt(0).toUpperCase()}</span>` : 
                                    '<i class="icon fas fa-question-circle"></i>';
                                div.innerHTML = fallback;
                            }
                        }} 
                    />`;
                })
            .with([P.string, undefined],
                ([name]) => this.renderLetterIcon(name))
            .exhaustive();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-app-icon": AppIcon;
    }
}
