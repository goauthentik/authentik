import "@goauthentik/admin/admin-settings/AdminSettingsForm";
import { AdminSettingsForm } from "@goauthentik/admin/admin-settings/AdminSettingsForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ModalForm";

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

import { AdminApi, Settings } from "@goauthentik/api";

@customElement("ak-admin-settings")
export class AdminSettingsPage extends AKElement {
    static get styles() {
        return [
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
    }

    @query("ak-admin-settings-form#form")
    form?: AdminSettingsForm;

    @state()
    settings?: Settings;

    constructor() {
        super();
        AdminSettingsPage.fetchSettings().then((settings) => {
            this.settings = settings;
        });
        this.save = this.save.bind(this);
        this.reset = this.reset.bind(this);
        this.addEventListener("ak-admin-setting-changed", this.handleUpdate.bind(this));
    }

    static async fetchSettings() {
        return await new AdminApi(DEFAULT_CONFIG).adminSettingsRetrieve();
    }

    async handleUpdate() {
        this.settings = await AdminSettingsPage.fetchSettings();
    }

    async save() {
        if (!this.form) {
            return;
        }
        await this.form.submit(new Event("submit"));
        this.settings = await AdminSettingsPage.fetchSettings();
    }

    async reset() {
        this.form?.resetForm();
    }

    render() {
        if (!this.settings) {
            return nothing;
        }
        return html`
            <ak-page-header icon="fa fa-cog" header="" description="">
                <span slot="header"> ${msg("System settings")} </span>
            </ak-page-header>
            <section class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-admin-settings-form id="form" .settings=${this.settings}>
                        </ak-admin-settings-form>
                    </div>
                    <div class="pf-c-card__footer">
                        <ak-spinner-button .callAction=${this.save} class="pf-m-primary"
                            >${msg("Save")}</ak-spinner-button
                        >
                        <ak-spinner-button .callAction=${this.reset} class="pf-m-secondary"
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
