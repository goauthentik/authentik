import { truncateWords } from "@goauthentik/common/utils";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Expand";
import { UserInterface } from "@goauthentik/user/UserInterface";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { Application } from "@goauthentik/api";

@customElement("ak-library-app")
export class LibraryApplication extends AKElement {
    @property({ attribute: false })
    application?: Application;

    @property({ type: Boolean })
    selected = false;

    @property()
    background = "";

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFCard,
            PFButton,
            PFAvatar,
            css`
                :host {
                    --icon-height: 4rem;
                    --icon-border: 0.25rem;
                }
                .pf-c-card {
                    height: 100%;
                    --pf-c-card--BoxShadow: var(--pf-global--BoxShadow--md);
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
                .pf-c-card__header {
                    min-height: 60px;
                    justify-content: space-between;
                    flex-direction: column;
                }
                .pf-c-card__header a {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                .icon {
                    font-size: var(--icon-height);
                    padding: var(--icon-border);
                    max-height: calc(var(--icon-height) + var(--icon-border) + var(--icon-border));
                    line-height: calc(var(--icon-height) + var(--icon-border) + var(--icon-border));
                }
                .expander {
                    flex-grow: 1;
                }
                .title {
                    text-align: center;
                }
            `,
        ];
    }

    renderIcon(): TemplateResult {
        if (this.application?.metaIcon) {
            if (this.application.metaIcon.startsWith("fa://")) {
                const icon = this.application.metaIcon.replaceAll("fa://", "");
                return html`<i class="icon fas ${icon}"></i>`;
            }
            return html`<img
                class="app-icon pf-c-avatar"
                src="${ifDefined(this.application.metaIcon)}"
                alt="${msg("Application Icon")}"
            />`;
        }
        return html`<span class="icon">${this.application?.name.charAt(0).toUpperCase()}</span>`;
    }

    render(): TemplateResult {
        if (!this.application) {
            return html`<ak-spinner></ak-spinner>`;
        }
        const me = rootInterface<UserInterface>()?.me;
        return html` <div
            class="pf-c-card pf-m-hoverable pf-m-compact ${this.selected
                ? "pf-m-selectable pf-m-selected"
                : ""}"
            style=${this.background !== "" ? `background: ${this.background} !important` : ""}
        >
            <div class="pf-c-card__header">
                <a
                    href="${ifDefined(this.application.launchUrl ?? "")}"
                    target="${ifDefined(this.application.openInNewTab ? "_blank" : undefined)}"
                >
                    ${this.renderIcon()}
                </a>
            </div>
            <div class="pf-c-card__title">
                <p class="title">
                    <a
                        href="${ifDefined(this.application.launchUrl ?? "")}"
                        target="${ifDefined(this.application.openInNewTab ? "_blank" : undefined)}"
                        >${this.application.name}</a
                    >
                </p>
            </div>
            <div class="expander"></div>
            <ak-expand>
                <div class="pf-c-content">
                    <small>${this.application.metaPublisher}</small>
                </div>
                ${truncateWords(this.application.metaDescription || "", 10)}
                ${rootInterface()?.uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser
                    ? html`
                          <a
                              class="pf-c-button pf-m-control pf-m-small pf-m-block"
                              href="/if/admin/#/core/applications/${this.application?.slug}"
                          >
                              <i class="fas fa-pencil-alt"></i>&nbsp;${msg("Edit")}
                          </a>
                      `
                    : html``}
            </ak-expand>
        </div>`;
    }
}
