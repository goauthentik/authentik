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

import { kebabCase } from "change-case";

import { msg, str } from "@lit/localize";
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

            .launch-wrapper {
                display: flex;
                flex-direction: column;

                &:hover {
                    text-decoration: none;
                }
            }

            .expander {
                flex-grow: 1;
            }

            .pf-c-card__title {
                text-align: center;

                display: box;
                display: -webkit-box;
                line-clamp: 2;
                -webkit-line-clamp: 2;
                box-orient: vertical;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }
        `,
    ];

    #openRACLaunchModal = () => {
        this.racEndpointLaunch?.show();
    };

    renderExpansion(application: Application) {
        const { me, uiConfig } = rootInterface<UserInterface>();

        return html`<ak-expand text-open=${msg("Details")} text-closed=${msg("Details")}>
            <div class="pf-c-content" part="card-expansion">
                <small>${application.metaPublisher}</small>
            </div>
            <div id="app-description" part="card-description">
                ${truncateWords(application.metaDescription || "", 10)}
            </div>
            ${uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser
                ? html`
                      <a
                          class="pf-c-button pf-m-control pf-m-small pf-m-block"
                          aria-label=${msg(str`Edit "${application.name}"`)}
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

        if (this.application.launchUrl === "goauthentik.io://providers/rac/launch") {
            return html`<div
                    part="card-header"
                    class="pf-c-card__header pf-m-pressable"
                    role="button"
                    aria-label=${msg(
                        str`Open Remote Access Control launcher for "${this.application.name}"`,
                    )}
                    @click=${this.#openRACLaunchModal}
                >
                    <ak-app-icon
                        part="card-header-icon"
                        size=${PFSize.Large}
                        name=${this.application.name}
                        icon=${ifPresent(this.application.metaIcon)}
                    ></ak-app-icon>
                </div>
                <div
                    @click=${this.#openRACLaunchModal}
                    id="app-title"
                    class="pf-c-card__title pf-m-pressable"
                    part="card-title"
                >
                    ${this.application.name}
                </div>
                <ak-library-rac-endpoint-launch .app=${this.application}>
                </ak-library-rac-endpoint-launch>`;
        }

        return html`<a
            class="launch-wrapper"
            part="card-header-link"
            aria-label=${msg(str`Open "${this.application.name}"`)}
            href=${ifPresent(this.application.launchUrl)}
            target=${ifPresent(this.application.openInNewTab, "_blank")}
        >
            <div class="pf-c-card__header" part="card-header">
                <ak-app-icon
                    part="card-header-icon"
                    size=${PFSize.Large}
                    name=${this.application.name}
                    icon=${ifPresent(this.application.metaIcon)}
                ></ak-app-icon>
            </div>
            <div id="app-title" class="pf-c-card__title" part="card-title">
                ${this.application.name}
            </div>
        </a>`;
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

        const classes = {
            "pf-m-selectable": this.selected,
            "pf-m-selected": this.selected,
        };

        const styles = this.background ? { background: this.background } : {};
        const applicationName = kebabCase(this.application.name);

        return html`<div
            role="gridcell"
            class="pf-c-card pf-m-hoverable pf-m-compact ${classMap(classes)}"
            style=${styleMap(styles)}
            data-application-name=${ifPresent(applicationName)}
            aria-labelledby="app-title"
            aria-describedby="app-description"
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
