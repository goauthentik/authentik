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

    render(): TemplateResult {
        // prettier-ignore
        return match([this.name, this.icon])
            .with([undefined, undefined],
                () => html`<div><i class="icon fas fa-question-circle"></i></div>`)
            .with([P._, P.string.startsWith("fa://")],
                ([_name, icon]) => html`<div><i class="icon fas ${icon.replaceAll("fa://", "")}"></i></div>`)
            .with([P._, P.string],
                ([_name, icon]) => html`<img class="icon pf-c-avatar" src="${icon}" alt="${msg("Application Icon")}" />`)
            .with([P.string, undefined],
                ([name]) => html`<span class="icon">${name.charAt(0).toUpperCase()}</span>`)
            .exhaustive();
    }
}

export default AppIcon;

declare global {
    interface HTMLElementTagNameMap {
        "ak-app-icon": AppIcon;
    }
}
