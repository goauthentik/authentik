import "@goauthentik/admin/applications/ProviderSelectModal";
import { iconHelperText } from "@goauthentik/admin/helperText";
import { DEFAULT_CONFIG, config } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/components/ak-file-input";
import "@goauthentik/components/ak-radio-input";
import "@goauthentik/components/ak-switch-input";
import "@goauthentik/components/ak-text-input";
import "@goauthentik/components/ak-textarea-input";
import { rootInterface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import "@goauthentik/elements/forms/ModalForm";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/ProxyForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    Application,
    CapabilitiesEnum,
    CoreApi,
    PolicyEngineMode,
    Provider,
} from "@goauthentik/api";

import "./components/ak-backchannel-input";
import "./components/ak-provider-search-input";

export const policyOptions = [
    {
        label: "any",
        value: PolicyEngineMode.Any,
        default: true,
        description: html`${msg("Any policy must match to grant access")}`,
    },
    {
        label: "all",
        value: PolicyEngineMode.All,
        description: html`${msg("All policies must match to grant access")}`,
    },
];

@customElement("ak-application-form")
export class ApplicationForm extends ModelForm<Application, string> {
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

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated application.");
        } else {
            return msg("Successfully created application.");
        }
    }

    async send(data: Application): Promise<Application | void> {
        let app: Application;
        data.backchannelProviders = this.backchannelProviders.map((p) => p.pk);
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
        const c = await config();
        if (c.capabilities.includes(CapabilitiesEnum.CanSaveMedia)) {
            const icon = this.getFormFiles()["metaIcon"];
            if (icon || this.clearIcon) {
                await new CoreApi(DEFAULT_CONFIG).coreApplicationsSetIconCreate({
                    slug: app.slug,
                    file: icon,
                    clear: this.clearIcon,
                });
            }
        } else {
            await new CoreApi(DEFAULT_CONFIG).coreApplicationsSetIconUrlCreate({
                slug: app.slug,
                filePathRequest: {
                    url: data.metaIcon || "",
                },
            });
        }
        return app;
    }

    handleConfirmBackchannelProviders({ items }: { items: Provider[] }) {
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
        ev.stopPropagation();
        if (!(ev instanceof InputEvent) || !ev.target) {
            return;
        }
        this.clearIcon = !!(ev.target as HTMLInputElement).checked;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-text-input
                name="name"
                value=${this.instance?.name}
                label=${msg("Name")}
                required
                help=${msg("Application's display Name.")}
            ></ak-text-input>
            <ak-text-input
                name="slug"
                value=${this.instance?.slug}
                label=${msg("Slug")}
                required
                help=${msg("Internal application name used in URLs.")}
            ></ak-text-input>
            <ak-text-input
                name="group"
                value=${this.instance?.group}
                label=${msg("Group")}
                help=${msg(
                    "Optionally enter a group name. Applications with identical groups are shown grouped together.",
                )}
            ></ak-text-input>
            <ak-provider-search-input
                name="provider"
                label=${msg("Provider")}
                value=${this.instance?.provider}
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
                    ></ak-text-input>
                    <ak-switch-input
                        name="openInNewTab"
                        ?checked=${first(this.instance?.openInNewTab, false)}
                        label=${msg("Open in new tab")}
                        help=${msg(
                            "If checked, the launch URL will open in a new browser tab or window from the user's application library.",
                        )}
                    >
                    </ak-switch-input>
                    ${rootInterface()?.config?.capabilities.includes(CapabilitiesEnum.CanSaveMedia)
                        ? html`<ak-file-input
                                  label="${msg("Icon")}"
                                  name="metaIcon"
                                  value=${this.instance?.metaIcon}
                                  current=${msg("Currently set to:")}
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
                              value=${first(this.instance?.metaIcon, "")}
                              help=${iconHelperText}
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
