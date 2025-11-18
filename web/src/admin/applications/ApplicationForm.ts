import "#admin/applications/ProviderSelectModal";
import "#components/ak-file-input";
import "#components/ak-radio-input";
import "#components/ak-slug-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#components/ak-textarea-input";
import "#elements/Alert";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/ModalForm";
import "#elements/forms/ProxyForm";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/ak-search-select";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "./components/ak-backchannel-input.js";
import "./components/ak-provider-search-input.js";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { CapabilitiesEnum, WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { navigate } from "#elements/router/RouterOutlet";
import { ifPresent } from "#elements/utils/attributes";

import { iconHelperText } from "#admin/helperText";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import { Application, CoreApi, Provider } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-application-form")
export class ApplicationForm extends WithCapabilitiesConfig(ModelForm<Application, string>) {
    #api = new CoreApi(DEFAULT_CONFIG);

    protected override async loadInstance(pk: string): Promise<Application> {
        const app = await this.#api.coreApplicationsRetrieve({
            slug: pk,
        });

        this.clearIcon = false;
        this.backchannelProviders = app.backchannelProvidersObj || [];

        return app;
    }

    @property({ attribute: false })
    public provider?: number;

    @state()
    protected backchannelProviders: Provider[] = [];

    @property({ type: Boolean })
    public clearIcon = false;

    protected override entityLabel = msg("Application");

    public override async send(applicationRequest: Application): Promise<Application | void> {
        applicationRequest.backchannelProviders = this.backchannelProviders.map((p) => p.pk);

        const currentSlug = this.instance?.slug;

        const app = await (currentSlug
            ? this.#api.coreApplicationsUpdate({
                  applicationRequest,
                  slug: currentSlug,
              })
            : this.#api.coreApplicationsCreate({ applicationRequest }));

        const nextSlug = app.slug;

        if (this.can(CapabilitiesEnum.CanSaveMedia)) {
            const icon = this.files().get("metaIcon");

            if (icon || this.clearIcon) {
                await this.#api.coreApplicationsSetIconCreate({
                    slug: nextSlug,
                    file: icon,
                    clear: this.clearIcon,
                });
            }
        } else {
            await this.#api.coreApplicationsSetIconUrlCreate({
                slug: nextSlug,
                filePathRequest: {
                    url: applicationRequest.metaIcon || "",
                },
            });
        }

        if (currentSlug && currentSlug !== nextSlug) {
            // TODO: This needs refining.
            this.instancePk = nextSlug;
            navigate(`/core/applications/${nextSlug}`);
        }

        return app;
    }

    #handleConfirmBackchannelProviders = (items: Provider[]) => {
        this.backchannelProviders = items;
        this.requestUpdate();

        return Promise.resolve();
    };

    #makeRemoveBackchannelProviderHandler = (provider: Provider) => {
        return () => {
            const idx = this.backchannelProviders.indexOf(provider);
            this.backchannelProviders.splice(idx, 1);
            this.requestUpdate();
        };
    };

    handleClearIcon(ev: Event) {
        ev.stopPropagation();
        if (!(ev instanceof InputEvent) || !ev.target) {
            return;
        }
        this.clearIcon = !!(ev.target as HTMLInputElement).checked;
    }

    public override renderForm(): TemplateResult {
        const alertMsg = msg(
            "Using this form will only create an Application. In order to authenticate with the application, you will have to manually pair it with a Provider.",
        );

        return html`
            ${this.instance ? nothing : html`<ak-alert level="pf-m-info">${alertMsg}</ak-alert>`}
            <ak-text-input
                name="name"
                autocomplete="off"
                placeholder=${msg("Type an application name...", {
                    id: "application.form.name.placeholder",
                })}
                value=${ifDefined(this.instance?.name)}
                label=${msg("Application Name", {
                    id: "application.form.name.label",
                })}
                spellcheck="false"
                required
                help=${msg("The name displayed in the application library.", {
                    id: "application.form.name.help",
                })}
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                autocomplete="off"
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                help=${msg("Internal application name used in URLs.", {
                    id: "application.form.slug.help",
                    desc: "Help text for the slug field in the application form",
                })}
                input-hint="code"
            ></ak-slug-input>
            <ak-text-input
                name="group"
                value=${ifDefined(this.instance?.group)}
                label=${msg("Group")}
                placeholder=${msg("e.g. Collaboration, Communication, Internal, etc.", {
                    id: "application.form.group.placeholder",
                    desc: "Placeholder text for the group field in the application form",
                })}
                help=${msg(
                    "Optionally enter a group name. Applications with identical groups are shown grouped together.",
                    {
                        id: "application.form.group.help",
                        desc: "Help text for the group field in the application form",
                    },
                )}
                input-hint="code"
            ></ak-text-input>
            <ak-provider-search-input
                name="provider"
                label=${msg("Provider")}
                value=${ifPresent(this.instance?.provider)}
                help=${msg("Select a provider that this application should use.", {
                    id: "application.form.provider.help",
                    desc: "Help text for the provider field in the application form",
                })}
                blankable
            ></ak-provider-search-input>
            <ak-backchannel-providers-input
                name="backchannelProviders"
                label=${msg("Backchannel Providers")}
                help=${msg(
                    "Select backchannel providers which augment the functionality of the main provider.",
                    {
                        id: "application.form.backchannel-providers.help",
                        desc: "Help text for the backchannel providers field in the application form",
                    },
                )}
                .providers=${this.backchannelProviders}
                .confirm=${this.#handleConfirmBackchannelProviders}
                .remover=${this.#makeRemoveBackchannelProviderHandler}
                .tooltip=${html`<pf-tooltip
                    position="top"
                    content=${msg("Add provider", {
                        id: "application.form.backchannel-providers.add-provider.tooltip",
                    })}
                ></pf-tooltip>`}
            >
            </ak-backchannel-providers-input>
            <ak-radio-input
                label=${msg("Policy engine mode", {
                    id: "application.form.policy-engine-mode.label",
                })}
                required
                name="policyEngineMode"
                .options=${policyEngineModes}
                .value=${this.instance?.policyEngineMode}
            ></ak-radio-input>
            <ak-form-group label="${msg("UI settings")}">
                <div class="pf-c-form">
                    <ak-text-input
                        name="metaLaunchUrl"
                        label=${msg("Launch URL")}
                        placeholder=${msg("https://...")}
                        value=${ifDefined(this.instance?.metaLaunchUrl)}
                        help=${msg(
                            "If left empty, authentik will try to extract the launch URL based on the selected provider.",
                        )}
                        input-hint="code"
                    ></ak-text-input>
                    <ak-switch-input
                        name="openInNewTab"
                        ?checked=${this.instance?.openInNewTab ?? false}
                        label=${msg("Open in new tab", {
                            id: "application.form.open-in-new-tab.label",
                        })}
                        help=${msg(
                            "If checked, the launch URL will open in a new browser tab or window from the user's application library.",
                            {
                                id: "application.form.open-in-new-tab.help",
                            },
                        )}
                    >
                    </ak-switch-input>
                    ${this.can(CapabilitiesEnum.CanSaveMedia)
                        ? html`<ak-file-input
                                  label="${msg("Icon")}"
                                  name="metaIcon"
                                  value=${ifPresent(this.instance?.metaIcon)}
                                  current=${msg("Currently set to:", {
                                      id: "application.form.icon.current",
                                  })}
                              ></ak-file-input>
                              ${this.instance?.metaIcon
                                  ? html`
                                        <ak-switch-input
                                            name=""
                                            label=${msg("Clear icon", {
                                                id: "application.form.clear-icon.label",
                                            })}
                                            help=${msg("Delete currently set icon.", {
                                                id: "application.form.clear-icon.help",
                                            })}
                                            @change=${this.handleClearIcon}
                                        ></ak-switch-input>
                                    `
                                  : nothing}`
                        : html` <ak-text-input
                              label=${msg("Icon", {
                                  id: "application.form.icon.label",
                              })}
                              name="metaIcon"
                              value=${this.instance?.metaIcon ?? ""}
                              help=${iconHelperText}
                          >
                          </ak-text-input>`}
                    <ak-text-input
                        label=${msg("Publisher", {
                            id: "application.form.publisher.label",
                        })}
                        name="metaPublisher"
                        value="${ifDefined(this.instance?.metaPublisher)}"
                    ></ak-text-input>
                    <ak-textarea-input
                        label=${msg("Description", {
                            id: "application.form.description.label",
                        })}
                        name="metaDescription"
                        value=${ifDefined(this.instance?.metaDescription)}
                    ></ak-textarea-input>
                </div>
            </ak-form-group>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-form": ApplicationForm;
    }
}
