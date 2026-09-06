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
import "#elements/ak-array-input";
import "#admin/applications/components/ak-application-link-input";
import "#admin/applications/components/ak-backchannel-input";
import "#admin/applications/components/ak-provider-search-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import type { RadioOption } from "#elements/forms/Radio";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { navigate } from "#elements/router/RouterOutlet";
import { ifPresent } from "#elements/utils/attributes";

import {
    akApplicationLinkInput,
    type IApplicationLinkInput,
} from "#admin/applications/components/ak-application-link-input";
import { policyEngineModes } from "#admin/policies/PolicyEngineModes";

import {
    AdminApi,
    AlignEnum,
    Application,
    ApplicationLink,
    CoreApi,
    FileList,
    Provider,
    UsageEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * Horizontal alignment of the heading above the additional-links row.
 *
 * Physical rather than logical: an administrator sets this once and every user
 * sees the result, whatever their locale. Logical values would hand a
 * right-to-left reader the mirror of what was chosen.
 *
 * No descriptions: three words that need none, and rendered inline they cost one
 * form row instead of six.
 */
const applicationLinkAlignments: RadioOption<AlignEnum>[] = [
    {
        label: msg("Left", {
            id: "applications.links.align.left",
            desc: "Text alignment option, one of Left/Center/Right. Aligns a heading to the left edge of a card.",
        }),
        value: AlignEnum.Left,
    },
    {
        label: msg("Center", {
            id: "applications.links.align.center",
            desc: "Text alignment option, one of Left/Center/Right. Centers a heading on a card.",
        }),
        value: AlignEnum.Center,
        default: true,
    },
    {
        label: msg("Right", {
            id: "applications.links.align.right",
            desc: "Text alignment option, one of Left/Center/Right. Aligns a heading to the right edge of a card.",
        }),
        value: AlignEnum.Right,
    },
];

/**
 * Application Form
 *
 * @prop {string} instancePk - The primary key of the instance to load.
 */
@customElement("ak-application-form")
export class ApplicationForm extends WithCapabilitiesConfig(ModelForm<Application, string>) {
    #api = aki(CoreApi);

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

    /**
     * The file library, fetched once for the whole form and handed to every
     * additional-link row. Rows never call the API themselves, so the number
     * of requests does not grow with the number of links.
     */
    @state()
    protected mediaFiles: FileList[] = [];

    #mediaRequested = false;

    /**
     * Loaded on first approach of the links section — hover or focus — rather
     * than on form load. The icon dropdown is optional and often untouched,
     * so its file list should not be fetched with the rest of the form.
     */
    protected loadMediaFiles = (): void => {
        if (this.#mediaRequested) return;
        this.#mediaRequested = true;
        aki(AdminApi)
            .adminFileList({ usage: UsageEnum.Media })
            .then((files) => {
                this.mediaFiles = files;
            })
            // The dropdown stays usable with the bundled glyphs alone.
            .catch(() => undefined);
    };

    /** Called after an upload, when the list genuinely changed. */
    protected refreshMediaFiles = (): void => {
        this.#mediaRequested = false;
        this.loadMediaFiles();
    };

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
                help=${msg("The name displayed in the Application Dashboard.")}
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
                            "If checked, the launch URL will open in a new browser tab or window from the user's Application Dashboard.",
                        )}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="metaHide"
                        ?checked=${this.instance?.metaHide ?? false}
                        label=${msg("Hide from Application Dashboard")}
                        help=${msg(
                            "If checked, this application will not be shown on the user's Application Dashboard.",
                        )}
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
                        help=${msg("The publisher is shown in the Application Dashboard.")}
                    ></ak-text-input>
                    <ak-textarea-input
                        label=${msg("Description")}
                        name="metaDescription"
                        placeholder=${msg("Type an optional description...")}
                        value=${ifDefined(this.instance?.metaDescription)}
                        help=${msg(
                            "The description is shown in the Application Dashboard and may provide additional information about the application to end users.",
                        )}
                    ></ak-textarea-input>
                </div>
            </ak-form-group>
            <ak-form-group
                label="${msg("Additional links", {
                    id: "applications.links.group",
                    desc: "Title of the form section configuring extra links shown under an application card, such as native client downloads.",
                })}"
            >
                <div class="pf-c-form">
                    <ak-switch-input
                        name="applicationLinks.enabled"
                        ?checked=${this.instance?.applicationLinks?.enabled ?? false}
                        label=${msg("Show additional links", {
                            id: "applications.links.enabled",
                            desc: "Label of the switch turning the extra links on for this application.",
                        })}
                        help=${msg(
                            "If checked, the links configured below are shown under this application's card.",
                            {
                                id: "applications.links.enabled.help",
                                desc: "Help text under the switch. 'Card' is the tile representing an application on the user dashboard.",
                            },
                        )}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="applicationLinks.address"
                        ?checked=${this.instance?.applicationLinks?.address ?? false}
                        label=${msg("Show copy address button", {
                            id: "applications.links.address",
                            desc: "Label of the switch showing a button that copies the application's web address to the clipboard.",
                        })}
                        help=${msg(
                            "If checked, a button that copies this application's address is shown alongside the links. The address is derived from the launch URL, never entered by hand.",
                            {
                                id: "applications.links.address.help",
                                desc: "Help text under the switch. 'Address' means the web address (URL) of the service, not a postal address.",
                            },
                        )}
                    >
                    </ak-switch-input>
                    <ak-text-input
                        label=${msg("Heading", {
                            id: "applications.links.title",
                            desc: "Label of the field holding a short caption displayed above the row of links, such as 'Native clients'.",
                        })}
                        name="applicationLinks.title"
                        value=${ifDefined(this.instance?.applicationLinks?.title)}
                        placeholder=${msg("Type an optional heading...", {
                            id: "applications.links.title.placeholder",
                            desc: "Placeholder inside the empty heading field.",
                        })}
                        help=${msg(
                            "Shown above the row of links on the card. Left out entirely when blank.",
                            {
                                id: "applications.links.title.help",
                                desc: "Help text under the heading field. 'Left out' means the heading is not rendered at all.",
                            },
                        )}
                    ></ak-text-input>
                    <ak-radio-input
                        label=${msg("Alignment", {
                            id: "applications.links.align",
                            desc: "Label of the Left/Center/Right choice positioning the heading horizontally.",
                        })}
                        name="applicationLinks.align"
                        inline
                        .options=${applicationLinkAlignments}
                        .value=${this.instance?.applicationLinks?.align ?? AlignEnum.Center}
                        help=${msg("Applies to the heading only. The links stay centered.", {
                            id: "applications.links.align.help",
                            desc: "Help text under the alignment choice, clarifying that the icons themselves do not move.",
                        })}
                    ></ak-radio-input>
                    <ak-form-element-horizontal
                        label=${msg("Links", {
                            id: "applications.links.items",
                            desc: "Label of the editable list of links. Each entry has a name, a web address and an icon.",
                        })}
                        name="applicationLinks.links"
                        @mouseenter=${this.loadMediaFiles}
                        @focusin=${this.loadMediaFiles}
                        @ak-application-link-files-changed=${this.refreshMediaFiles}
                    >
                        <ak-array-input
                            .items=${this.instance?.applicationLinks?.links ?? []}
                            .newItem=${() => ({ label: "", url: "", icon: "" })}
                            .row=${(link?: ApplicationLink, index?: number) =>
                                akApplicationLinkInput({
                                    ".applicationLink": link,
                                    ".files": this.mediaFiles,
                                    // Column headings on the first row only.
                                    "?headers": index === 0,
                                    "style": "width: 100%",
                                    "name": "application-link",
                                } as unknown as IApplicationLinkInput)}
                        >
                        </ak-array-input>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Shown under the application card in the user dashboard. URLs are limited to http and https. For a platform or vendor logo, upload it to the file library and pick it here.",
                                {
                                    id: "applications.links.items.help",
                                    desc: "Help text under the list of links. 'File library' is the administration section holding uploaded images.",
                                },
                            )}
                        </p>
                    </ak-form-element-horizontal>
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
