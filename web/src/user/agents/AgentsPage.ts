import "./PersonasList";

import Styles from "../LibraryPage/ak-library-impl.css";

import { PaginatedResponse } from "#common/api/responses";

import { AKElement } from "#elements/Base";

import { Application } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement, state } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-agents")
export class AgentsPage extends AKElement {
    static styles = [PFPage, PFForm, PFContent, PFFormControl, Styles];

    @state()
    apps?: PaginatedResponse<Application>;

    render() {
        return html`<div class="pf-c-page__main">
            <div class="pf-c-page__header pf-c-content">
                <h1 class="pf-c-page__header pf-c-content">${msg("Agents")}</h1>
            </div>
            <main class="pf-c-page__main-section">
                <ak-user-persona-list></ak-user-persona-list>
            </main>
        </div>`;
    }
}
