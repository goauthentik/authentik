import { t } from "@lingui/macro";
import {
    css,
    CSSResult,
    customElement,
    html,
    LitElement,
    property,
    TemplateResult,
} from "lit-element";
import { ifDefined } from "lit-html/directives/if-defined";
import { until } from "lit-html/directives/until";
import { Application } from "@goauthentik/api";
import { me } from "../api/Users";
import { truncate } from "../utils";
import AKGlobal from "../authentik.css";
import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import { uiConfig } from "./config";

@customElement("ak-library-app")
export class LibraryApplication extends LitElement {
    @property({ attribute: false })
    application?: Application;

    @property({ type: Boolean })
    selected = false;

    @property()
    background: string = "";

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFCard,
            PFButton,
            PFAvatar,
            AKGlobal,
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

    render(): TemplateResult {
        if (!this.application) {
            return html`<ak-spinner></ak-spinner>`;
        }
        return html` <div
            class="pf-c-card pf-m-hoverable pf-m-compact ${this.selected
                ? "pf-m-selectable pf-m-selected"
                : ""}"
            style="background: ${this.background} !important"
        >
            <div class="pf-c-card__header">
                ${this.application.metaIcon
                    ? html`<a href="${ifDefined(this.application.launchUrl ?? "")}"
                          ><img
                              class="app-icon pf-c-avatar"
                              src="${ifDefined(this.application.metaIcon)}"
                              alt="${t`Application Icon`}"
                      /></a>`
                    : html`<i class="fas fas fa-share-square"></i>`}
                ${until(
                    uiConfig().then((config) => {
                        if (!config.enabledFeatures.applicationEdit) {
                            return html``;
                        }
                        return me().then((u) => {
                            if (!u.user.isSuperuser) return html``;
                            return html`
                                <a
                                    class="pf-c-button pf-m-control pf-m-small"
                                    href="/if/admin/#/core/applications/${this.application?.slug}"
                                >
                                    <i class="fas fa-pencil-alt"></i>
                                </a>
                            `;
                        });
                    }),
                )}
            </div>
            <div class="pf-c-card__title">
                <p>
                    <a href="${ifDefined(this.application.launchUrl ?? "")}"
                        >${this.application.name}</a
                    >
                </p>
                <div class="pf-c-content">
                    <small>${this.application.metaPublisher}</small>
                </div>
            </div>
            <div class="pf-c-card__body">${truncate(this.application.metaDescription, 35)}</div>
        </div>`;
    }
}
