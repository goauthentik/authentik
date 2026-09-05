import "#elements/AppIcon";

import { PFSize } from "#common/enums";

import { AKControlElement } from "#elements/ControlElement";
import { renderModal } from "#elements/dialogs";
import { AKFormSubmittedEvent } from "#elements/forms/events";
import { type Spread } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { FileUploadForm } from "#admin/files/FileUploadForm";

import { AdminFileCreateRequest, ApplicationLink, FileList } from "@goauthentik/api";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property, queryAll, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFInputGroup from "@patternfly/patternfly/components/InputGroup/input-group.css";

export interface IApplicationLinkInput {
    applicationLink: ApplicationLink;
}

/** Dispatched after an upload so the parent form refreshes its file list. */
export const FILES_CHANGED_EVENT = "ak-application-link-files-changed";

/**
 * Mirrors the server-side check in `ApplicationLinkSerializer`. An
 * administrator-supplied URL could otherwise carry a `javascript:` scheme,
 * which on an identity provider is stored XSS.
 */
const LEGAL_SCHEMES = ["http://", "https://"];
const hasLegalScheme = (url: string) =>
    LEGAL_SCHEMES.some((scheme) => url.slice(0, scheme.length).toLowerCase() === scheme);

const DEFAULT_ICON = "fa://fa-link";

interface IconChoice {
    value: string;
    label: string;
}

/**
 * Bundled glyphs offered in the dropdown.
 *
 * Deliberately limited to Font Awesome *solid* icons: the icon font shipped
 * with PatternFly is `fa-solid-900` only, so brand glyphs — Apple, Android,
 * Windows and the like — have CSS rules but no glyph in the font and render
 * blank. Platform logos are uploaded by the administrator instead, which also
 * keeps authentik from distributing third-party brand marks.
 */
const ICON_GROUPS: { label: string; icons: IconChoice[] }[] = [
    {
        label: "Applications",
        icons: [
            { value: "fa://fa-mobile", label: "Mobile app" },
            { value: "fa://fa-desktop", label: "Desktop app" },
            { value: "fa://fa-download", label: "Download" },
        ],
    },
    {
        label: "Information",
        icons: [
            { value: "fa://fa-book", label: "Documentation" },
            { value: "fa://fa-life-ring", label: "Support" },
            { value: "fa://fa-globe", label: "Website" },
            { value: "fa://fa-file-code", label: "Source code" },
            { value: "fa://fa-link", label: "Generic link" },
        ],
    },
];

/**
 * Vendor marks authentik already serves for its authentication sources. They
 * are reused here rather than shipping a second copy, and they cover the two
 * cases the solid icon font cannot: the Apple and Google stores.
 */
const SOURCE_ICONS: IconChoice[] = [
    { value: "/static/authentik/sources/apple.svg", label: "Apple" },
    { value: "/static/authentik/sources/google.svg", label: "Google" },
    { value: "/static/authentik/sources/github.svg", label: "GitHub" },
    { value: "/static/authentik/sources/gitlab.svg", label: "GitLab" },
];

ICON_GROUPS.push({ label: "authentik icons", icons: SOURCE_ICONS });

const BUNDLED_VALUES = new Set(ICON_GROUPS.flatMap((group) => group.icons.map((i) => i.value)));

@customElement("ak-application-link-input")
export class ApplicationLinkInput extends AKControlElement<ApplicationLink> {
    static styles = [
        PFInputGroup,
        PFFormControl,
        PFButton,
        css`
            :host {
                display: block;
                width: 100%;
            }
            .row {
                display: flex;
                flex-direction: column;
                gap: var(--pf-global--spacer--xs, 0.25rem);
                width: 100%;
            }
            .pf-c-input-group {
                width: 100%;
            }
            .pf-c-input-group input,
            .pf-c-input-group select {
                min-width: 0;
            }
            .pf-c-input-group input#link-label {
                flex: 1 1 8rem;
            }
            .pf-c-input-group input#link-url {
                flex: 2 1 12rem;
            }
            .pf-c-input-group select#link-icon {
                flex: 1 1 auto;
            }
            .preview {
                display: grid;
                place-items: center;
                flex: 0 0 auto;
                width: 2.25rem;
                border: 1px solid var(--pf-global--BorderColor--300);
                border-inline-end: none;
                background: var(--pf-global--BackgroundColor--200);
                color: var(--pf-global--Color--200);
            }
            /* Drive the component's own variables rather than its rendered
               part: width and height have no effect on an inline <i>. */
            .preview ak-app-icon {
                --icon-height: 1rem;
                --icon-border: 0;
            }
            .preview ak-app-icon {
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .preview ak-app-icon::part(icon) {
                display: block;
                line-height: 1;
                filter: none;
            }
            .preview ak-app-icon::part(image) {
                width: 88%;
                height: 88%;
                object-fit: contain;
            }
        `,
    ];

    @property({ type: Object, attribute: false })
    applicationLink: ApplicationLink = { label: "", url: "", icon: "" };

    /**
     * Supplied by the parent form, which fetches the file library once for
     * every row. Rows never call the API themselves, so the number of
     * requests does not grow with the number of links.
     */
    @property({ type: Array, attribute: false })
    files: FileList[] = [];

    @state()
    private previewIcon = "";

    @queryAll(".ak-form-control")
    controls?: HTMLInputElement[];

    @property({ type: String })
    public name: string | null = null;

    firstUpdated(): void {
        this.previewIcon = this.applicationLink.icon || "";
    }

    private notifyChange = () => {
        this.dispatchEvent(new Event("change", { composed: true, bubbles: true }));
    };

    /** Reuses authentik's own upload form rather than adding another. */
    private openUploadModal = (invocationEvent?: Event) => {
        invocationEvent?.stopPropagation();
        const form = new FileUploadForm();
        let created: AdminFileCreateRequest | null = null;

        form.addEventListener(AKFormSubmittedEvent.eventName, (event) => {
            created = (event as AKFormSubmittedEvent<AdminFileCreateRequest>).response;
        });

        return renderModal(form, {
            invokerElement:
                invocationEvent?.target instanceof HTMLElement ? invocationEvent.target : this,
            size: PFSize.Medium,
            onDispose: (disposeEvent) => {
                const { target } = disposeEvent || {};
                if (!(target instanceof HTMLDialogElement) || target.returnValue !== "submitted") {
                    return;
                }
                if (!created) return;
                // Ask the form to refresh its list so the new file is offered.
                this.dispatchEvent(
                    new CustomEvent(FILES_CHANGED_EVENT, { bubbles: true, composed: true }),
                );
            },
        });
    };

    toJSON(): ApplicationLink {
        return Object.fromEntries(
            Array.from(this.controls ?? []).map((control) => [control.name, control.value]),
        ) as unknown as ApplicationLink;
    }

    get valid() {
        const link = this.toJSON();
        const url = link?.url ?? "";
        return Boolean(link?.label) && hasLegalScheme(url) && URL.canParse(url);
    }

    render() {
        const onIconChange = (event: Event) => {
            this.previewIcon = (event.target as HTMLSelectElement).value;
            this.notifyChange();
        };

        const current = this.applicationLink.icon ?? "";
        // The stored value is the file URL, not its name: ak-app-icon feeds
        // it straight into an <img src>, and unlike `meta_icon` there is no
        // server-side name-to-URL resolution for these links.
        const known =
            !current ||
            BUNDLED_VALUES.has(current) ||
            this.files.some((file) => file.url === current);
        const uploadLabel = msg("Upload an icon");

        return html` <div class="row">
            <div class="pf-c-input-group">
                <input
                    type="text"
                    @change=${this.notifyChange}
                    value=${ifPresent(this.applicationLink.label)}
                    id="link-label"
                    class="pf-c-form-control ak-form-control"
                    name="label"
                    placeholder=${msg("Label")}
                    required
                    tabindex="1"
                />
                <input
                    type="url"
                    @change=${this.notifyChange}
                    value=${ifPresent(this.applicationLink.url)}
                    id="link-url"
                    class="pf-c-form-control ak-form-control pf-m-monospace"
                    autocomplete="off"
                    required
                    placeholder=${msg("URL")}
                    name="url"
                    tabindex="1"
                />
            </div>
            <div class="pf-c-input-group">
                <span class="preview" title=${msg("Icon preview")}>
                    <ak-app-icon
                        size=${PFSize.Small}
                        name=""
                        icon=${this.previewIcon || DEFAULT_ICON}
                    ></ak-app-icon>
                </span>
                <select
                    id="link-icon"
                    class="pf-c-form-control ak-form-control"
                    name="icon"
                    @change=${onIconChange}
                    tabindex="1"
                >
                    <option value="" ?selected=${!current}>${msg("Default link icon")}</option>
                    ${known
                        ? nothing
                        : html`<option value=${current} selected>
                              ${msg("Current value")}: ${current}
                          </option>`}
                    ${ICON_GROUPS.map(
                        (group) => html`
                            <optgroup label=${group.label}>
                                ${group.icons.map(
                                    (icon) => html`
                                        <option
                                            value=${icon.value}
                                            ?selected=${current === icon.value}
                                        >
                                            ${icon.label}
                                        </option>
                                    `,
                                )}
                            </optgroup>
                        `,
                    )}
                    ${this.files.length
                        ? html`<optgroup label=${msg("Uploaded files")}>
                              ${this.files.map(
                                  (file) => html`
                                      <option value=${file.url} ?selected=${current === file.url}>
                                          ${file.name}
                                      </option>
                                  `,
                              )}
                          </optgroup>`
                        : nothing}
                </select>
                <button
                    @click=${this.openUploadModal}
                    type="button"
                    class="pf-c-button pf-m-control"
                    aria-label=${uploadLabel}
                    title=${uploadLabel}
                    tabindex="1"
                >
                    <i class="fas fa-upload" aria-hidden="true"></i>
                </button>
            </div>
        </div>`;
    }
}

export function akApplicationLinkInput(properties: IApplicationLinkInput) {
    return html`<ak-application-link-input
        ${spread(properties as unknown as Spread)}
    ></ak-application-link-input>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-application-link-input": ApplicationLinkInput;
    }
}
