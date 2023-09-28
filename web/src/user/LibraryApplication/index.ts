import { PFSize } from "@goauthentik/app/elements/Spinner";
import { truncateWords } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-app-icon";
import { AKElement, rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Expand";
import { UserInterface } from "@goauthentik/user/UserInterface";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { styleMap } from "lit/directives/style-map.js";

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
    }

    renderExpansion(application: Application) {
        const me = rootInterface<UserInterface>()?.me;

        return html`<ak-expand textOpen=${msg("Less details")} textClosed=${msg("More details")}>
            <div class="pf-c-content">
                <small>${application.metaPublisher}</small>
            </div>
            ${truncateWords(application.metaDescription || "", 10)}
            ${rootInterface()?.uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser
                ? html`
                      <a
                          class="pf-c-button pf-m-control pf-m-small pf-m-block"
                          href="/if/admin/#/core/applications/${application?.slug}"
                      >
                          <i class="fas fa-edit"></i>&nbsp;${msg("Edit")}
                      </a>
                  `
                : html``}
        </ak-expand>`;
    }

    render(): TemplateResult {
        if (!this.application) {
            return html`<ak-spinner></ak-spinner>`;
        }

        const me = rootInterface<UserInterface>()?.me;
        const expandable =
            (rootInterface()?.uiConfig?.enabledFeatures.applicationEdit && me?.user.isSuperuser) ||
            this.application.metaPublisher !== "" ||
            this.application.metaDescription !== "";

        const classes = { "pf-m-selectable pf-m-selected": this.selected };
        const styles = this.background ? { background: this.background } : {};

        return html` <div
            class="pf-c-card pf-m-hoverable pf-m-compact ${classMap(classes)}"
            style=${styleMap(styles)}
        >
            <div class="pf-c-card__header">
                <a
                    href="${ifDefined(this.application.launchUrl ?? "")}"
                    target="${ifDefined(this.application.openInNewTab ? "_blank" : undefined)}"
                >
                    <ak-app-icon size=${PFSize.Large} .app=${this.application}></ak-app-icon>
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
            ${expandable ? this.renderExpansion(this.application) : nothing}
        </div>`;
    }
}
