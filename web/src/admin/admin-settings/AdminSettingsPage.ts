import "@goauthentik/admin/admin-settings/AdminSettingsForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { convertToTitle } from "@goauthentik/common/utils";
import "@goauthentik/components/events/ObjectChangelog";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/EmptyState";
import "@goauthentik/elements/Markdown";
import "@goauthentik/elements/PageHeader";
import "@goauthentik/elements/Tabs";
import "@goauthentik/elements/buttons/ModalButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/buttons/SpinnerButton";
import "@goauthentik/elements/forms/ModalForm";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

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
    static get styles(): CSSResult[] {
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
    @property({ attribute: false })
    settings?: Settings;

    loadSettings(): void {
        new AdminApi(DEFAULT_CONFIG).adminSettingsRetrieve().then((settings) => {
            this.settings = settings;
        });
    }

    firstUpdated(): void {
        this.loadSettings();
    }

    async save(): void {
        const form = this.shadowRoot?.querySelector<AdminSettingsForm>("ak-admin-settings-form");
        if (!form) {
            return;
        }
        await form.submit(new Event("submit"));
        this.resetForm();
    }

    resetForm(): void {
        const form = this.shadowRoot?.querySelector<AdminSettingsForm>("ak-admin-settings-form");
        if (!form) {
            return;
        }
        this.loadSettings();
        form.settings = this.settings;
        form.resetForm();
    }

    render(): TemplateResult {
        if (!this.settings) {
            return html``;
        }
        return html`
            <ak-page-header icon="fa fa-cog" header="" description="">
                <span slot="header"> ${msg("System settings")} </span>
            </ak-page-header>
            <section class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <ak-admin-settings-form id="form" .settings=${this.settings}>
                </ak-admin-settings-form>
                <ak-spinner-button
                    .callAction=${async () => {
                        await this.save();
                    }}
                    class="pf-m-primary"
                    >${msg("Save")}</ak-spinner-button
                >
                <ak-spinner-button
                    .callAction=${() => {
                        this.resetForm();
                    }}
                    class="pf-m-secondary"
                    >${msg("Cancel")}</ak-spinner-button
                >
            </section>
        `;
    }
}
