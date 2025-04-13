import "@goauthentik/admin/applications/ProviderSelectModal";
import { iconHelperText } from "@goauthentik/admin/helperText";
import {
    removeApplicationIcon,
    setApplicationIcon,
    setApplicationIconUrl,
} from "@goauthentik/common/api/applications";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { MessageLevel } from "@goauthentik/common/messages";
import "@goauthentik/components/ak-file-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import "@goauthentik/elements/Alert.js";
import {
    CapabilitiesEnum,
    WithCapabilitiesConfig,
} from "@goauthentik/elements/Interface/capabilitiesProvider";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/ModalForm";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import { showMessage } from "@goauthentik/elements/messages/MessageContainer";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { Application, CoreApi, Provider } from "@goauthentik/api";

import { policyOptions } from "./PolicyOptions.js";
import "./components/ak-backchannel-input";
import "./components/ak-provider-search-input";

@customElement("ak-application-form")
export class ApplicationForm extends WithCapabilitiesConfig(ModelForm<Application, string>) {
    constructor() {
        super();
        this.handleConfirmBackchannelProviders = this.handleConfirmBackchannelProviders.bind(this);
        this.makeRemoveBackchannelProviderHandler =
            this.makeRemoveBackchannelProviderHandler.bind(this);
    }

    async loadInstance(pk: string): Promise<Application> {
        const app = await new CoreApi(DEFAULT_CONFIG).coreApplicationsRetrieve({
            slug: pk,
        });
        this.clearIcon = false;
        this.backchannelProviders = app.backchannelProvidersObj || [];
        return app;
    }

    @property({ attribute: false })
    provider?: number;

    @state()
    backchannelProviders: Provider[] = [];

    @property({ type: Boolean })
    clearIcon = false;

    @state()
    iconError = "";

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated application.")
            : msg("Successfully created application.");
    }

    async send(data: Application): Promise<Application | void> {
        // Reset icon error
        this.iconError = "";

        let app: Application;
        data.backchannelProviders = this.backchannelProviders.map((p) => p.pk);
        try {
            if (this.instance) {
                app = await new CoreApi(DEFAULT_CONFIG).coreApplicationsUpdate({
                    slug: this.instance.slug,
                    applicationRequest: data,
                });
            } else {
                app = await new CoreApi(DEFAULT_CONFIG).coreApplicationsCreate({
                    applicationRequest: data,
                });
            }
        } catch (error: any) {
            // Let the base form handle error display
            throw error;
        }

        // Create mutable copy of the app for modifications
        const mutableApp = { ...app };

        if (this.can(CapabilitiesEnum.CanSaveMedia)) {
            const icon = this.getFormFiles()["metaIcon"];
            let attemptedIconOperation = false;
            try {
                let iconResponse;
                let iconSuccess = true;

                if (this.clearIcon) {
                    attemptedIconOperation = true;
                    // Clear the icon
                    iconResponse = await removeApplicationIcon(app.slug);
                    if (iconResponse && !iconResponse.error) {
                        showMessage({
                            level: MessageLevel.success,
                            message: msg("Application icon cleared successfully"),
                        });
                    } else {
                        // Let the base form handle error display
                        throw new Error(iconResponse?.error || "Unknown error clearing icon");
                    }
                } else if (icon) {
                    attemptedIconOperation = true;
                    // Upload new icon file
                    iconResponse = await setApplicationIcon(app.slug, icon);
                    if (!iconResponse.error && iconResponse.meta_icon) {
                        mutableApp.metaIcon = iconResponse.meta_icon;
                        showMessage({
                            level: MessageLevel.success,
                            message: msg("Application icon updated successfully"),
                        });
                    } else {
                        // Let the base form handle error display
                        throw new Error(iconResponse.error);
                    }
                } else if (
                    data.metaIcon &&
                    (!this.instance || data.metaIcon !== this.instance.metaIcon)
                ) {
                    attemptedIconOperation = true;
                    // Set icon URL
                    iconResponse = await setApplicationIconUrl(app.slug, data.metaIcon);
                    if (!iconResponse.error && iconResponse.meta_icon) {
                        mutableApp.metaIcon = iconResponse.meta_icon;
                        showMessage({
                            level: MessageLevel.success,
                            message: msg("Application icon URL updated successfully"),
                        });
                    } else {
                        // Let the base form handle error display
                        throw new Error(iconResponse.error);
                    }
                }

                // If any icon operation was attempted and failed, do not return the app
                if (attemptedIconOperation && !iconSuccess) {
                    return;
                }
            } catch (e: unknown) {
                // Let the base form handle error display
                // Clear the file input after an error
                const fileInput = this.shadowRoot?.querySelector('ak-file-input[name="metaIcon"] input[type="file"]') as HTMLInputElement;
                if (fileInput) {
                    fileInput.value = "";
                }
                throw e;
            }
        }

        // Only return the app if all operations succeeded
        return mutableApp;
    }

    handleConfirmBackchannelProviders(items: Provider[]) {
        this.backchannelProviders = items;
        this.requestUpdate();
        return Promise.resolve();
    }

    makeRemoveBackchannelProviderHandler(provider: Provider) {
        return () => {
            const idx = this.backchannelProviders.indexOf(provider);
            this.backchannelProviders.splice(idx, 1);
            this.requestUpdate();
        };
    }

    handleClearIcon(ev: Event) {
        const target = ev.target as HTMLInputElement;
        this.clearIcon = target.checked;
    }

    // Validate URL format for icon URL
    validateIconUrl(url: string): boolean {
        if (!url) return true; // Empty is valid

        // Check if it's a Font Awesome icon reference
        if (url.startsWith("fa://")) return true;

        // Check if it's a valid URL
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    renderForm(): TemplateResult {
        const alertMsg = msg(
            "Using this form will only create an Application. In order to authenticate with the application, you will have to manually pair it with a Provider.",
        );

        return html`<form class="pf-c-form pf-m-horizontal">
            ${this.instance ? nothing : html`<ak-alert level="pf-m-info">${alertMsg}</ak-alert>`}
            <ak-text-input
                name="name"
                value=${ifDefined(this.instance?.name)}
                label=${msg("Name")}
                required
                help=${msg("Application's display Name.")}
            ></ak-text-input>
            <ak-text-input
                name="slug"
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                help=${msg("Internal application name used in URLs.")}
                inputHint="code"
            ></ak-text-input>
            <ak-text-input
                name="group"
                value=${ifDefined(this.instance?.group)}
                label=${msg("Group")}
                help=${msg(
                    "Optionally enter a group name. Applications with identical groups are shown grouped together.",
                )}
                inputHint="code"
            ></ak-text-input>
            <ak-provider-search-input
                name="provider"
                label=${msg("Provider")}
                value=${ifDefined(this.instance?.provider ?? undefined)}
                help=${msg("Select a provider that this application should use.")}
                blankable
            ></ak-provider-search-input>
            <ak-backchannel-providers-input
                name="backchannelProviders"
                label=${msg("Backchannel Providers")}
                help=${msg(
                    "Select backchannel providers which augment the functionality of the main provider.",
                )}
                .providers=${this.backchannelProviders}
                .confirm=${this.handleConfirmBackchannelProviders}
                .remover=${this.makeRemoveBackchannelProviderHandler}
                .tooltip=${html`<pf-tooltip
                    position="top"
                    content=${msg("Add provider")}
                ></pf-tooltip>`}
            >
            </ak-backchannel-providers-input>
            <ak-radio-input
                label=${msg("Policy engine mode")}
                required
                name="policyEngineMode"
                .options=${policyOptions}
                .value=${this.instance?.policyEngineMode}
            ></ak-radio-input>
            <ak-form-group>
                <span slot="header"> ${msg("UI settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-text-input
                        name="metaLaunchUrl"
                        label=${msg("Launch URL")}
                        value=${ifDefined(this.instance?.metaLaunchUrl)}
                        help=${msg(
                            "If left empty, authentik will try to extract the launch URL based on the selected provider.",
                        )}
                        inputHint="code"
                    ></ak-text-input>
                    <ak-switch-input
                        name="openInNewTab"
                        ?checked=${this.instance?.openInNewTab ?? false}
                        label=${msg("Open in new tab")}
                        help=${msg(
                            "If checked, the launch URL will open in a new browser tab or window from the user's application library.",
                        )}
                    >
                    </ak-switch-input>
                    ${this.can(CapabilitiesEnum.CanSaveMedia)
                        ? html`<ak-file-input
                                  label="${msg("Icon")}"
                                  name="metaIcon"
                                  value=${ifDefined(this.instance?.metaIcon ?? undefined)}
                                  current=${msg("Currently set to:")}
                                  .errorMessage=${this.iconError}
                              ></ak-file-input>
                              ${this.instance?.metaIcon
                                  ? html`
                                        <ak-switch-input
                                            name=""
                                            label=${msg("Clear icon")}
                                            help=${msg("Delete currently set icon.")}
                                            @change=${this.handleClearIcon}
                                        ></ak-switch-input>
                                    `
                                  : html``}`
                        : html` <ak-text-input
                              label=${msg("Icon")}
                              name="metaIcon"
                              value=${this.instance?.metaIcon ?? ""}
                              help=${iconHelperText}
                              .errorMessage=${this.iconError}
                              @input=${(e: Event) => {
                                  const target = e.target as HTMLInputElement;
                                  if (!this.validateIconUrl(target.value)) {
                                      this.iconError = msg("Invalid URL format");
                                  } else {
                                      this.iconError = "";
                                  }
                              }}
                          >
                          </ak-text-input>`}
                    <ak-text-input
                        label=${msg("Publisher")}
                        name="metaPublisher"
                        value="${ifDefined(this.instance?.metaPublisher)}"
                    ></ak-text-input>
                    <ak-textarea-input
                        label=${msg("Description")}
                        name="metaDescription"
                        value=${ifDefined(this.instance?.metaDescription)}
                    ></ak-textarea-input>
                </div>
            </ak-form-group>
        </form>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-form": ApplicationForm;
    }
}
