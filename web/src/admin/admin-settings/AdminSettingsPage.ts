import "#admin/admin-settings/AdminSettingsForm";
import "#components/ak-page-header";
import "#components/events/ObjectChangelog";
import "#elements/CodeMirror";
import "#elements/EmptyState";
import "#elements/Tabs";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/ModalForm";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";

import { AdminSettingsForm } from "#admin/admin-settings/AdminSettingsForm";

import { AdminApi, Settings } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, query, state } from "lit/decorators.js";

import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-admin-settings")
export class AdminSettingsPage extends AKElement {
    static styles = [
        PFBase,
        PFButton,
        PFPage,
        PFGrid,
        PFContent,
        PFCard,
        PFDescriptionList,
        PFForm,
        PFFormControl,
        PFBanner,
    ];

    @query("ak-admin-settings-form#form")
    protected form?: AdminSettingsForm;

    @state()
    protected settings?: Settings;

    constructor() {
        super();

        this.#refresh();

        this.addEventListener("ak-admin-setting-changed", this.#refresh);
    }

    #refresh = () => {
        return new AdminApi(DEFAULT_CONFIG).adminSettingsRetrieve().then((settings) => {
            this.settings = settings;
        });
    };

    #save = () => {
        return this.form?.submit(new SubmitEvent("submit")).then(this.#refresh);
    };

    #reset = () => {
        return this.form?.reset();
    };

    render() {
        if (!this.settings) return nothing;

        return html`
            <ak-page-header icon="fa fa-cog" header="${msg("System settings")}"> </ak-page-header>
            <section class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-admin-settings-form id="form" .settings=${this.settings}>
                        </ak-admin-settings-form>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-spinner-button .callAction=${this.#save} class="pf-m-primary"
                            >${msg("Save")}</ak-spinner-button
                        >
                        <ak-spinner-button .callAction=${this.#reset} class="pf-m-secondary"
                            >${msg("Cancel")}</ak-spinner-button
                        >
                    </div>
                </div>
            </section>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-settings": AdminSettingsPage;
    }
}
