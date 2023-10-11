import { MessageLevel } from "@goauthentik/common/messages";
import {
    ShowHintController,
    ShowHintControllerHost,
} from "@goauthentik/components/ak-hint/ShowHintController";
import "@goauthentik/components/ak-hint/ak-hint";
import "@goauthentik/components/ak-hint/ak-hint-body";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/buttons/ActionButton/ak-action-button";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";

import { html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-application-wizard-hint")
export class AkApplicationWizardHint extends AKElement implements ShowHintControllerHost {
    static get styles() {
        return [PFPage];
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

    renderHint() {
        return html` <section class="pf-c-page__main-section pf-m-no-padding-mobile">
            <ak-hint>
                <ak-hint-body>
                    <p>
                        Authentik has a new Application Wizard that can configure both an
                        application and its authentication provider at the same time.
                        <a href="(link to docs)">Learn more about the wizard here.</a>
                    </p>
                    <ak-action-button
                        class="pf-m-secondary"
                        .apiRequest=${() => {
                            showMessage({
                                message: "This would have shown the wizard",
                                level: MessageLevel.success,
                            });
                        }}
                        >Create with Wizard</ak-action-button
                    ></ak-hint-body
                >
                ${this.showHintController.render()}
            </ak-hint>
        </section>`;
    }

    render() {
        return this.showHint || this.forceHint ? this.renderHint() : nothing;
    }
}

export default AkApplicationWizardHint;
