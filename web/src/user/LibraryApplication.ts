import { truncateWords } from "@goauthentik/common/utils";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
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
                .pf-c-card {
                    height: 100%;
                }
                i.pf-icon {
                    height: 36px;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }
                .pf-c-avatar {
                    --pf-c-avatar--BorderRadius: 0;
                }
                .pf-c-card__header {
                    min-height: 60px;
                    justify-content: space-between;
                }
                .pf-c-card__header a {
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    margin-right: 0.25em;
                }
            `,
        ];
    }

    renderIcon(): TemplateResult {
        if (this.application?.metaIcon) {
            if (this.application.metaIcon.startsWith("fa://")) {
                const icon = this.application.metaIcon.replaceAll("fa://", "");
                return html`<i class="fas ${icon}"></i>`;
            }
            return html`<img
                class="app-icon pf-c-avatar"
                src="${ifDefined(this.application.metaIcon)}"
                alt="${msg("Application Icon")}"
            />`;
        }
        return html`<i class="fas fa-share-square"></i>`;
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
            style="background: ${this.background} !important"
        >
            <div class="pf-c-card__header">
                <a
                    href="${ifDefined(this.application.launchUrl ?? "")}"
                    target="${ifDefined(this.application.openInNewTab ? "_blank" : undefined)}"
                >
                    ${this.renderIcon()}
                </a>
                ${rootInterface()?.uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser
                    ? html`
                          <a
                              class="pf-c-button pf-m-control pf-m-small"
                              href="/if/admin/#/core/applications/${this.application?.slug}"
                          >
                              <i class="fas fa-pencil-alt"></i>
                          </a>
                      `
                    : html``}
            </div>
            <div class="pf-c-card__title">
                <p>
                    <a
                        href="${ifDefined(this.application.launchUrl ?? "")}"
                        target="${ifDefined(this.application.openInNewTab ? "_blank" : undefined)}"
                        >${this.application.name}</a
                    >
                </p>
                <div class="pf-c-content">
                    <small>${this.application.metaPublisher}</small>
                </div>
            </div>
            <div class="pf-c-card__body">
                ${truncateWords(this.application.metaDescription || "", 35)}
            </div>
        </div>`;
    }
}
