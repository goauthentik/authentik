import "#elements/AppIcon";
import "#elements/Expand";
import "#user/LibraryApplication/RACLaunchEndpointModal";

import { PFSize } from "#common/enums";
import { globalAK } from "#common/global";
import { rootInterface } from "#common/theme";
import { truncateWords } from "#common/utils";

import { AKElement } from "#elements/Base";
import { SlottedTemplateResult } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import type { UserInterface } from "#user/index.entrypoint";
import type { RACLaunchEndpointModal } from "#user/LibraryApplication/RACLaunchEndpointModal";

import { Application } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { styleMap } from "lit/directives/style-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-library-app")
export class LibraryApplication extends AKElement {
    @property({ attribute: false })
    application?: Application;

    @property({ type: Boolean })
    selected = false;

    @property()
    background = "";

    @query("ak-library-rac-endpoint-launch")
    racEndpointLaunch?: RACLaunchEndpointModal;

    static styles: CSSResult[] = [
        PFBase,
        PFCard,
        PFButton,
        css`
            .pf-c-card {
                --pf-c-card--BoxShadow: var(--pf-global--BoxShadow--md);
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
            a:hover {
                text-decoration: none;
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

    renderExpansion(application: Application) {
        const { me, uiConfig } = rootInterface<UserInterface>();

        return html`<ak-expand textOpen=${msg("Fewer details")} textClosed=${msg("More details")}>
            <div class="pf-c-content">
                <small>${application.metaPublisher}</small>
            </div>
            ${truncateWords(application.metaDescription || "", 10)}
            ${uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser
                ? html`
                      <a
                          class="pf-c-button pf-m-control pf-m-small pf-m-block"
                          href="${globalAK().api
                              .base}if/admin/#/core/applications/${application?.slug}"
                      >
                          <i class="fas fa-edit" aria-hidden="true"></i>&nbsp;${msg("Edit")}
                      </a>
                  `
                : nothing}
        </ak-expand>`;
    }

    renderLaunch(): SlottedTemplateResult {
        if (!this.application) {
            return nothing;
        }
        if (this.application?.launchUrl === "goauthentik.io://providers/rac/launch") {
            return html`<div class="pf-c-card__header">
                    <a
                        @click=${() => {
                            this.racEndpointLaunch?.show();
                        }}
                    >
                        <ak-app-icon
                            size=${PFSize.Large}
                            name=${this.application.name}
                            icon=${ifPresent(this.application.metaIcon)}
                        ></ak-app-icon>
                    </a>
                </div>
                <div class="pf-c-card__title">
                    <a
                        @click=${() => {
                            this.racEndpointLaunch?.show();
                        }}
                    >
                        ${this.application.name}
                    </a>
                </div>
                <ak-library-rac-endpoint-launch .app=${this.application}>
                </ak-library-rac-endpoint-launch>`;
        }
        return html`<div class="pf-c-card__header">
                <a
                    href="${ifPresent(this.application.launchUrl ?? "")}"
                    target="${ifPresent(this.application.openInNewTab, "_blank")}"
                >
                    <ak-app-icon
                        size=${PFSize.Large}
                        name=${this.application.name}
                        icon=${ifPresent(this.application.metaIcon)}
                    ></ak-app-icon>
                </a>
            </div>
            <div class="pf-c-card__title">
                <a
                    href="${ifPresent(this.application.launchUrl ?? "")}"
                    target="${ifPresent(this.application.openInNewTab, "_blank")}"
                    >${this.application.name}</a
                >
            </div>`;
    }

    render(): TemplateResult {
        if (!this.application) {
            return html`<ak-spinner></ak-spinner>`;
        }

        const { me, uiConfig } = rootInterface<UserInterface>();

        const expandable =
            (uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser) ||
            this.application.metaPublisher !== "" ||
            this.application.metaDescription !== "";

        const classes = { "pf-m-selectable": this.selected, "pf-m-selected": this.selected };
        const styles = this.background ? { background: this.background } : {};
        return html` <div
            class="pf-c-card pf-m-hoverable pf-m-compact ${classMap(classes)}"
            style=${styleMap(styles)}
        >
            ${this.renderLaunch()}
            <div class="expander"></div>
            ${expandable ? this.renderExpansion(this.application) : nothing}
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-library-app": LibraryApplication;
    }
}
