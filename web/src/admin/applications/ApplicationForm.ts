import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import "#components/ak-file-search-input";
import "#components/ak-radio-input";
import "#components/ak-slug-input";
import "#components/ak-switch-input";
import "#components/ak-text-input";
import "#components/ak-textarea-input";
import "#elements/Alert";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/ModalForm";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/ak-search-select";
import "#admin/applications/ak-provider-table";
import "#admin/applications/components/ak-backchannel-input";
import "#admin/applications/components/ak-provider-search-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { ModelForm } from "#elements/forms/ModelForm";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { navigate } from "#elements/router/RouterOutlet";
import { ifPresent } from "#elements/utils/attributes";

import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import { Application, CoreApi, Provider, UsageEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * Application Form
 *
 * @prop {string} instancePk - The primary key of the instance to load.
 */
@customElement("ak-application-form")
export class ApplicationForm extends WithCapabilitiesConfig(ModelForm<Application, string>) {
    #api = new CoreApi(DEFAULT_CONFIG);

    public static override verboseName = msg("Application");
    public static override verboseNamePlural = msg("Applications");

    protected override async loadInstance(pk: string): Promise<Application> {
        const app = await this.#api.coreApplicationsRetrieve({
            slug: pk,
        });

        this.backchannelProviders = app.backchannelProvidersObj || [];

        return app;
    }

    @property({ attribute: false })
    public provider: number | null = null;

    @state()
    protected backchannelProviders: Provider[] = [];

    public override reset(): void {
        super.reset();
        this.backchannelProviders = [];
    }

    public override getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated application.")
            : msg("Successfully created application.");
    }

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

        if (currentSlug && currentSlug !== nextSlug) {
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

    //#region Rendering

    protected override renderForm(): TemplateResult {
        const alertMsg = msg(
            "Using this form will only create an Application. In order to authenticate with the application, you will have to manually pair it with a Provider.",
        );
        const providerFromInstance = this.instance?.provider;
        const providerValue = providerFromInstance ?? this.provider;
        const providerPrefilled = !this.instance && this.provider !== null;

        return html`
            ${this.instance || this.provider
                ? null
                : html`<ak-alert level="pf-m-info">${alertMsg}</ak-alert>`}
            <ak-text-input
                name="name"
                autocomplete="off"
                placeholder=${msg("Type an application name...")}
                value=${ifDefined(this.instance?.name)}
                label=${msg("Application Name")}
                spellcheck="false"
                required
                help=${msg("The name displayed in the application library.")}
            ></ak-text-input>
            <ak-slug-input
                name="slug"
                value=${ifDefined(this.instance?.slug)}
                label=${msg("Slug")}
                required
                help=${msg("Internal application name used in URLs.")}
                placeholder=${msg("e.g. my-application")}
                input-hint="code"
            ></ak-slug-input>
            <ak-text-input
                name="group"
                value=${ifDefined(this.instance?.group)}
                label=${msg("Group")}
                placeholder=${msg("e.g. Collaboration, Communication, Internal, etc.")}
                help=${msg(
                    "Optionally enter a group name. Applications with identical groups are shown grouped together.",
                )}
                input-hint="code"
            ></ak-text-input>
            <ak-provider-search-input
                name="provider"
                label=${msg("Provider")}
                .value=${providerValue}
                .readOnly=${providerPrefilled}
                ?blankable=${!providerPrefilled}
                help=${msg("Select a provider that this application should use.")}
            ></ak-provider-search-input>
            <ak-backchannel-providers-input
                name="backchannelProviders"
                label=${msg("Backchannel Providers")}
                help=${msg(
                    "Select backchannel providers which augment the functionality of the main provider.",
                )}
                .providers=${this.backchannelProviders}
                .confirm=${this.#handleConfirmBackchannelProviders}
                .remover=${this.#makeRemoveBackchannelProviderHandler}
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
                        label=${msg("Open in new tab")}
                        help=${msg(
                            "Whether the launch URL will open in a new browser tab or window from the user's application library.",
                        )}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="metaHide"
                        ?checked=${this.instance?.metaHide ?? false}
                        label=${msg("Hide from User Dashboard")}
                        help=${msg("Whether this application will be shown on the User Dashboard.")}
                    >
                    </ak-switch-input>
                    <ak-file-search-input
                        name="metaIcon"
                        label=${msg("Icon")}
                        value=${ifPresent(this.instance?.metaIcon)}
                        .usage=${UsageEnum.Media}
                        help=${msg(
                            "Select from uploaded files, or type a Font Awesome icon (fa://fa-icon-name) or URL.",
                        )}
                        blankable
                    ></ak-file-search-input>
                    <ak-text-input
                        label=${msg("Publisher")}
                        name="metaPublisher"
                        value="${ifDefined(this.instance?.metaPublisher)}"
                        placeholder=${msg("Type an optional publisher name...")}
                        help=${msg("The publisher is shown in the application library.")}
                    ></ak-text-input>
                    <ak-textarea-input
                        label=${msg("Description")}
                        name="metaDescription"
                        placeholder=${msg("Type an optional description...")}
                        value=${ifDefined(this.instance?.metaDescription)}
                        help=${msg(
                            "The description is shown in the application library and may provide additional information about the application to end users.",
                        )}
                    ></ak-textarea-input>
                </div>
            </ak-form-group>
        `;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-form": ApplicationForm;
    }
}
