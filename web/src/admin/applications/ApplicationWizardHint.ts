import "@goauthentik/admin/applications/wizard/ak-application-wizard";
import {
    ShowHintController,
    ShowHintControllerHost,
} from "@goauthentik/components/ak-hint/ShowHintController";
import "@goauthentik/components/ak-hint/ak-hint";
import "@goauthentik/components/ak-hint/ak-hint-body";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/Label";
import "@goauthentik/elements/buttons/ActionButton/ak-action-button";
import { getURLParam } from "@goauthentik/elements/router/RouteMatch";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { styleMap } from "lit/directives/style-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFLabel from "@patternfly/patternfly/components/Label/label.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

const closeButtonIcon = html`<svg
    fill="currentColor"
    height="1em"
    width="1em"
    viewBox="0 0 352 512"
    aria-hidden="true"
    role="img"
    style="vertical-align: -0.125em;"
>
    <path
        d="M242.72 256l100.07-100.07c12.28-12.28 12.28-32.19 0-44.48l-22.24-22.24c-12.28-12.28-32.19-12.28-44.48 0L176 189.28 75.93 89.21c-12.28-12.28-32.19-12.28-44.48 0L9.21 111.45c-12.28 12.28-12.28 32.19 0 44.48L109.28 256 9.21 356.07c-12.28 12.28-12.28 32.19 0 44.48l22.24 22.24c12.28 12.28 32.2 12.28 44.48 0L176 322.72l100.07 100.07c12.28 12.28 32.2 12.28 44.48 0l22.24-22.24c12.28-12.28 12.28-32.19 0-44.48L242.72 256z"
    ></path>
</svg>`;

@customElement("ak-application-wizard-hint")
export class AkApplicationWizardHint extends AKElement implements ShowHintControllerHost {
    static get styles() {
        return [PFButton, PFPage, PFLabel];
    }

    @property({ type: Boolean, attribute: "show-hint" })
    forceHint: boolean = false;

    @state()
    showHint: boolean = true;

    showHintController: ShowHintController;

    constructor() {
        super();
        this.showHintController = new ShowHintController(
            this,
            "202310-application-wizard-announcement",
        );
    }

    renderReminder() {
        const sectionStyles = {
            paddingBottom: "0",
            marginBottom: "-0.5rem",
            marginRight: "0.0625rem",
            textAlign: "right",
        };
        const textStyle = { maxWidth: "60ch" };

        return html`<section
            class="pf-c-page__main-section pf-m-no-padding-mobile"
            style="${styleMap(sectionStyles)}"
        >
            <span class="pf-c-label">
                <a class="pf-c-label__content" @click=${this.showHintController.show}>
                    <span class="pf-c-label__text" style="${styleMap(textStyle)}">
                        ${msg("One hint, 'New Application Wizard', is currently hidden")}
                    </span>
                    <button
                        aria-disabled="false"
                        aria-label="Restore Application Wizard Hint "
                        class="pf-c-button pf-m-plain"
                        type="button"
                        data-ouia-safe="true"
                    >
                        ${closeButtonIcon}
                    </button>
                </a>
            </span>
        </section>`;
    }

    renderHint() {
        return html` <section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <ak-hint>
                <ak-hint-body>
                    <p>
                        You can now configure both an application and its authentication provider at
                        the same time with our new Application Wizard.
                        <!-- <a href="(link to docs)">Learn more about the wizard here.</a> -->
                    </p>

                    <ak-application-wizard
                        .open=${getURLParam("createWizard", false)}
                        .showButton=${false}
                    ></ak-application-wizard>
                </ak-hint-body>
                ${this.showHintController.render()}
            </ak-hint>
        </section>`;
    }

    render() {
        return this.showHint || this.forceHint ? this.renderHint() : this.renderReminder();
    }
}

export default AkApplicationWizardHint;
