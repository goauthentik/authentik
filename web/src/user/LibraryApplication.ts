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
                    color: var(--ak-global--Color--100);
                    padding: var(--icon-border);
                    max-height: calc(var(--icon-height) + var(--icon-border) + var(--icon-border));
                    line-height: calc(var(--icon-height) + var(--icon-border) + var(--icon-border));
                    filter: drop-shadow(5px 5px 5px rgba(128, 128, 128, 0.25));
                }
                .expander {
                    flex-grow: 1;
                }
                .pf-c-card__title {
                    text-align: center;
                    /* This is not ideal as it hard limits us to 2 lines of text for the title
                    of the application. In theory that should be fine for most cases, but ideally
                    we don't do this */
                    height: 48px;
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
                class="icon pf-c-avatar"
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
                <a
                    href="${ifDefined(this.application.launchUrl ?? "")}"
                    target="${ifDefined(this.application.openInNewTab ? "_blank" : undefined)}"
                    >${this.application.name}</a
                >
            </div>
            <div class="expander"></div>
            <ak-expand textOpen=${msg("Less details")} textClosed=${msg("More details")}>
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
