import "./DiscoverForm";

import Styles from "../LibraryPage/ak-library-impl.css";

import { AKElement } from "#elements/Base";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { customElement } from "lit/decorators.js";

import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-discovery")
export class DiscoverPage extends AKElement {
    static styles = [PFPage, PFForm, PFContent, PFFormControl, Styles];

    render() {
        return html`<div class="pf-c-page__main">
            <div class="pf-c-page__header pf-c-content">
                <h1 class="pf-c-page__header pf-c-content">${msg("Discover")}</h1>
            </div>
            <main class="pf-c-page__main-section">
                <ak-discover-form></ak-discover-form>
            </main>
        </div>`;
    }
}
