import { gettext } from "django";
import { CSSResult, customElement, html, LitElement, TemplateResult } from "lit-element";

import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";
import PFGallery from "@patternfly/patternfly/layouts/Gallery/gallery.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFDescriptionList from "@patternfly/patternfly/components/DescriptionList/description-list.css";
import PFSizing from "@patternfly/patternfly/utilities/Sizing/sizing.css";
import PFFlex from "@patternfly/patternfly/utilities/Flex/flex.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";
import AKGlobal from "../../authentik.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import { SourcesApi, StagesApi, UserSetting } from "authentik-api";
import { DEFAULT_CONFIG } from "../../api/Config";
import { until } from "lit-html/directives/until";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/Tabs";
import "./UserDetailsPage";
import "./UserTokenList";
import "./settings/UserSettingsAuthenticatorTOTP";
import "./settings/UserSettingsAuthenticatorStatic";
import "./settings/UserSettingsAuthenticatorWebAuthnDevices";
import "./settings/UserSettingsPassword";
import "./settings/SourceSettingsOAuth";

@customElement("ak-user-settings")
export class UserSettingsPage extends LitElement {

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFFlex, PFDisplay, PFGallery, PFContent, PFCard, PFDescriptionList, PFSizing, PFForm, PFFormControl, AKGlobal];
    }

    renderStageSettings(stage: UserSetting): TemplateResult {
        switch (stage.component) {
            case "ak-user-settings-authenticator-webauthn":
                return html`<ak-user-settings-authenticator-webauthn objectId=${stage.objectUid}>
                </ak-user-settings-authenticator-webauthn>`;
            case "ak-user-settings-password":
                return html`<ak-user-settings-password objectId=${stage.objectUid}>
                </ak-user-settings-password>`;
            case "ak-user-settings-authenticator-totp":
                return html`<ak-user-settings-authenticator-totp objectId=${stage.objectUid}>
                </ak-user-settings-authenticator-totp>`;
            case "ak-user-settings-authenticator-static":
                return html`<ak-user-settings-authenticator-static objectId=${stage.objectUid}>
                </ak-user-settings-authenticator-static>`;
            default:
                return html`<p>${gettext(`Error: unsupported stage settings: ${stage.component}`)}</p>`;
        }
    }

    renderSourceSettings(source: UserSetting): TemplateResult {
        switch (source.component) {
            case "ak-user-settings-source-oauth":
                return html`<ak-user-settings-source-oauth objectId=${source.objectUid}>
                </ak-user-settings-source-oauth>`;
            default:
                return html`<p>${gettext(`Error: unsupported source settings: ${source.component}`)}</p>`;
        }
    }

    render(): TemplateResult {
        return html`<div class="pf-c-page">
            <main role="main" class="pf-c-page__main" tabindex="-1">
                <section class="pf-c-page__main-section pf-m-light">
                    <div class="pf-c-content">
                        <h1>
                            <i class="pf-icon pf-icon-user"></i>
                            ${gettext("User Settings")}
                        </h1>
                        <p>${gettext("Configure settings relevant to your user profile.")}</p>
                    </div>
                </section>
                <ak-tabs ?vertical="${true}" style="height: 100%;">
                    <section slot="page-1" data-tab-title="${gettext("User details")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                        <ak-user-details></ak-user-details>
                    </section>
                    <section slot="page-2" data-tab-title="${gettext("Tokens")}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                        <ak-user-token-list></ak-user-token-list>
                    </section>
                    ${until(new StagesApi(DEFAULT_CONFIG).stagesAllUserSettings({}).then((stages) => {
                        return stages.map((stage) => {
                            return html`<section slot="page-${stage.objectUid}" data-tab-title="${ifDefined(stage.title)}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                                ${this.renderStageSettings(stage)}
                            </section>`;
                        });
                    }))}
                    ${until(new SourcesApi(DEFAULT_CONFIG).sourcesAllUserSettings({}).then((source) => {
                        return source.map((stage) => {
                            return html`<section slot="page-${stage.objectUid}" data-tab-title="${ifDefined(stage.title)}" class="pf-c-page__main-section pf-m-no-padding-mobile">
                                ${this.renderSourceSettings(stage)}
                            </section>`;
                        });
                    }))}
                </ak-tabs>
            </main>
        </div>`;
    }

}
