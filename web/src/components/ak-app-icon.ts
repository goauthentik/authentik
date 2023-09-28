import { AKElement } from "@goauthentik/app/elements/Base";
import { PFSize } from "@goauthentik/app/elements/Spinner";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFFAIcons from "@patternfly/patternfly/base/patternfly-fa-icons.css";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";

import { Application } from "@goauthentik/api";

@customElement("ak-app-icon")
export class AppIcon extends AKElement {
    @property({ attribute: false })
    app?: Application;

    @property()
    size?: PFSize;

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

    render(): TemplateResult {
        if (!this.app) {
            return html`<div><i class="icon fas fa-question-circle"></i></div>`;
        }
        if (this.app?.metaIcon) {
            if (this.app.metaIcon.startsWith("fa://")) {
                const icon = this.app.metaIcon.replaceAll("fa://", "");
                return html`<div><i class="icon fas ${icon}"></i></div>`;
            }
            return html`<img
                class="icon pf-c-avatar"
                src="${ifDefined(this.app.metaIcon)}"
                alt="${msg("Application Icon")}"
            />`;
        }
        return html`<span class="icon">${this.app?.name.charAt(0).toUpperCase()}</span>`;
    }
}

export default AppIcon;
