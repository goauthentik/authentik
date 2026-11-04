import "#admin/admin-settings/AdminSettingsForm";
import "#admin/events/ObjectChangelog";
import "#elements/CodeEditor";
import "#elements/EmptyState";
import "#elements/Tabs";
import "#elements/buttons/ModalButton";
import "#elements/buttons/SpinnerButton/ak-spinner-button";
import "#elements/forms/ModalForm";
import PFBanner from "@patternfly/patternfly/components/Banner/banner.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { aki } from "#common/api/client";
import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { setPageDetails } from "#elements/router/meta";

import { AdminSettingsForm } from "#admin/admin-settings/AdminSettingsForm";

import { AdminApi, Settings } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing, PropertyValues } from "lit";
import { customElement, query, state } from "lit/decorators.js";

@customElement("ak-admin-settings")
export class AdminSettingsPage extends AKElement {
    static styles = [
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

    public override connectedCallback(): void {
        super.connectedCallback();
        this.#refresh();
    }

    #refresh = () => {
        return aki(AdminApi)
            .adminSettingsRetrieve()
            .then((settings) => {
                this.settings = settings;
            });
    };

    renderBanner() {
        // Double the delta to account for variance in multiple server instances
        const delta = globalAK().config.cacheTimeoutSystemSettings * 2;

        const formatted = new Intl.DurationFormat("default", {
            style: "long",
        }).format({
            seconds: delta,
        });

        return html`<div class="pf-c-banner pf-m-info">
            ${msg(str`Changes to system settings will take up to ${formatted} to become effective.`)}
        </div>`;
    }

    render() {
        if (!this.settings) return nothing;

        return html`
            ${this.renderBanner()}
            <main class="pf-c-page__main-section pf-m-no-padding-mobile pf-l-grid pf-m-gutter">
                <div class="pf-c-card">
                    <div class="pf-c-card__body">
                        <ak-admin-settings-form
                            id="form"
                            .settings=${this.settings}
                            @ak-form-submitted=${{ handleEvent: this.#refresh, passive: true }}
                        >
                        </ak-admin-settings-form>
                    </div>
                </div>
            </main>
        `;
    }

    updated(changed: PropertyValues<this>) {
        super.updated(changed);

        setPageDetails({
            icon: "fa fa-cog",
            header: msg("System settings"),
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-admin-settings": AdminSettingsPage;
    }
}
