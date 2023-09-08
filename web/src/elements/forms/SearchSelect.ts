import { PreventFormSubmit } from "@goauthentik/app/elements/forms/helpers";
import { EVENT_REFRESH } from "@goauthentik/common/constants";
import { ascii_letters, digits, groupBy, randomString } from "@goauthentik/common/utils";
import { adaptCSS } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import { CustomEmitterElement } from "@goauthentik/elements/utils/eventEmitter";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html, render } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-search-select")
export class SearchSelect<T> extends CustomEmitterElement(AKElement) {
    @property()
    query?: string;

    @property({ attribute: false })
    objects?: T[];

    @property({ attribute: false })
    selectedObject?: T;

    @property()
    name?: string;

    @property({ type: Boolean })
    open = false;

    @property({ type: Boolean })
    blankable = false;

    @property()
    placeholder: string = msg("Select an object.");

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFFormControl, PFSelect];
    }

    @property({ attribute: false })
    fetchObjects!: (query?: string) => Promise<T[]>;

    @property({ attribute: false })
    renderElement!: (element: T) => string;

    @property({ attribute: false })
    renderDescription?: (element: T) => TemplateResult;

    @property({ attribute: false })
    value!: (element: T | undefined) => unknown;

    @property({ attribute: false })
    selected?: (element: T, elements: T[]) => boolean;

    @property()
    emptyOption = "---------";

    @property({ attribute: false })
    groupBy: (items: T[]) => [string, T[]][] = (items: T[]): [string, T[]][] => {
        return groupBy(items, () => {
            return "";
        });
    };

    scrollHandler?: () => void;
    observer: IntersectionObserver;
    dropdownUID: string;
    dropdownContainer: HTMLDivElement;
    isFetchingData = false;

    constructor() {
        super();
        if (!document.adoptedStyleSheets.includes(PFDropdown)) {
            document.adoptedStyleSheets = adaptCSS([...document.adoptedStyleSheets, PFDropdown]);
        }
        this.dropdownContainer = document.createElement("div");
        this.observer = new IntersectionObserver(() => {
            this.open = false;
            this.shadowRoot
                ?.querySelectorAll<HTMLInputElement>(
                    ".pf-c-form-control.pf-c-select__toggle-typeahead",
                )
                .forEach((input) => {
                    input.blur();
                });
        });
        this.observer.observe(this);
        this.dropdownUID = `dropdown-${randomString(10, ascii_letters + digits)}`;
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    shouldUpdate(changedProperties: Map<string, any>) {
        if (changedProperties.has("selectedObject")) {
            this.dispatchCustomEvent("ak-change", {
                value: this.selectedObject,
            });
        }
        return true;
    }

    toForm(): unknown {
        if (!this.objects) {
            throw new PreventFormSubmit(msg("Loading options..."));
        }
        return this.value(this.selectedObject) || "";
    }

    firstUpdated(): void {
        this.updateData();
    }

    updateData(): void {
        if (this.isFetchingData) {
            return;
        }
        this.isFetchingData = true;
        this.fetchObjects(this.query).then((objects) => {
            objects.forEach((obj) => {
                if (this.selected && this.selected(obj, objects || [])) {
                    this.selectedObject = obj;
                }
            });
            this.objects = objects;
            this.isFetchingData = false;
        });
    }

    connectedCallback(): void {
        super.connectedCallback();
        this.dropdownContainer = document.createElement("div");
        this.dropdownContainer.dataset["managedBy"] = "ak-search-select";
        document.body.append(this.dropdownContainer);
        this.updateData();
        this.addEventListener(EVENT_REFRESH, this.updateData);
        this.scrollHandler = () => {
            this.requestUpdate();
        };
        window.addEventListener("scroll", this.scrollHandler);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        this.removeEventListener(EVENT_REFRESH, this.updateData);
        if (this.scrollHandler) {
            window.removeEventListener("scroll", this.scrollHandler);
        }
        this.dropdownContainer.remove();
        this.observer.disconnect();
    }

    /*
     * This is a little bit hacky. Because we mainly want to use this field in modal-based forms,
     * rendering this menu inline makes the menu not overlay over top of the modal, and cause
     * the modal to scroll.
     * Hence, we render the menu into the document root, hide it when this menu isn't open
     * and remove it on disconnect
     * Also to move it to the correct position we're getting this elements's position and use that
     * to position the menu
     * The other downside this has is that, since we're rendering outside of a shadow root,
     * the pf-c-dropdown CSS needs to be loaded on the body.
     */
    renderMenu(): void {
        if (!this.objects) {
            return;
        }
        const pos = this.getBoundingClientRect();
        let groupedItems = this.groupBy(this.objects);
        let shouldRenderGroups = true;
        if (groupedItems.length === 1) {
            if (groupedItems[0].length < 1 || groupedItems[0][0] === "") {
                shouldRenderGroups = false;
            }
        }
        if (groupedItems.length === 0) {
            shouldRenderGroups = false;
            groupedItems = [["", []]];
        }
        const renderGroup = (items: T[], tabIndexStart: number): TemplateResult => {
            return html`${items.map((obj, index) => {
                let desc = undefined;
                if (this.renderDescription) {
                    desc = this.renderDescription(obj);
                }
                return html`
                    <li>
                        <button
                            class="pf-c-dropdown__menu-item ${desc === undefined
                                ? ""
                                : "pf-m-description"}"
                            role="option"
                            @click=${() => {
                                this.selectedObject = obj;
                                this.open = false;
                            }}
                            tabindex=${index + tabIndexStart}
                        >
                            ${desc === undefined
                                ? this.renderElement(obj)
                                : html`
                                      <div class="pf-c-dropdown__menu-item-main">
                                          ${this.renderElement(obj)}
                                      </div>
                                      <div class="pf-c-dropdown__menu-item-description">
                                          ${desc}
                                      </div>
                                  `}
                        </button>
                    </li>
                `;
            })}`;
        };
        render(
            html`<div
                class="pf-c-dropdown pf-m-expanded"
                style="position: fixed; inset: 0px auto auto 0px; z-index: 9999; transform: translate(${pos.x}px, ${pos.y +
                this.offsetHeight}px); width: ${pos.width}px; ${this.open
                    ? ""
                    : "visibility: hidden;"}"
            >
                <ul
                    class="pf-c-dropdown__menu pf-m-static"
                    role="listbox"
                    style="max-height:50vh;overflow-y:auto;"
                    id=${this.dropdownUID}
                    tabindex="0"
                >
                    ${this.blankable
                        ? html`
                              <li>
                                  <button
                                      class="pf-c-dropdown__menu-item"
                                      role="option"
                                      @click=${() => {
                                          this.selectedObject = undefined;
                                          this.open = false;
                                      }}
                                      tabindex="0"
                                  >
                                      ${this.emptyOption}
                                  </button>
                              </li>
                          `
                        : html``}
                    ${shouldRenderGroups
                        ? html`${groupedItems.map(([group, items], idx) => {
                              return html`
                                  <section class="pf-c-dropdown__group">
                                      <h1 class="pf-c-dropdown__group-title">${group}</h1>
                                      <ul>
                                          ${renderGroup(items, idx)}
                                      </ul>
                                  </section>
                              `;
                          })}`
                        : html`${renderGroup(groupedItems[0][1], 0)}`}
                </ul>
            </div>`,
            this.dropdownContainer,
            { host: this },
        );
    }

    render(): TemplateResult {
        this.renderMenu();
        let value = "";
        if (!this.objects) {
            value = msg("Loading...");
        } else if (this.selectedObject) {
            value = this.renderElement(this.selectedObject);
        } else if (this.blankable) {
            value = this.emptyOption;
        }
        return html`<div class="pf-c-select">
            <div class="pf-c-select__toggle pf-m-typeahead">
                <div class="pf-c-select__toggle-wrapper">
                    <input
                        class="pf-c-form-control pf-c-select__toggle-typeahead"
                        type="text"
                        placeholder=${this.placeholder}
                        spellcheck="false"
                        @input=${(ev: InputEvent) => {
                            this.query = (ev.target as HTMLInputElement).value;
                            this.updateData();
                        }}
                        @focus=${() => {
                            this.open = true;
                            this.renderMenu();
                        }}
                        @blur=${(ev: FocusEvent) => {
                            // For Safari, we get the <ul> element itself here when clicking on one of
                            // it's buttons, as the container has tabindex set
                            if (
                                ev.relatedTarget &&
                                (ev.relatedTarget as HTMLElement).id === this.dropdownUID
                            ) {
                                return;
                            }
                            // Check if we're losing focus to one of our dropdown items, and if such don't blur
                            if (ev.relatedTarget instanceof HTMLButtonElement) {
                                const parentMenu = ev.relatedTarget.closest(
                                    "ul.pf-c-dropdown__menu.pf-m-static",
                                );
                                if (parentMenu && parentMenu.id === this.dropdownUID) {
                                    return;
                                }
                            }
                            this.open = false;
                            this.renderMenu();
                        }}
                        .value=${value}
                    />
                </div>
            </div>
        </div>`;
    }
}
