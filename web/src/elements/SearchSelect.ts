import { AKElement } from "@goauthentik/elements/Base";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, html, render } from "lit";
import { customElement, property } from "lit/decorators.js";

import AKGlobal from "@goauthentik/common/styles/authentik.css";
import PFForm from "@patternfly/patternfly/components/Form/form.css";
import PFFormControl from "@patternfly/patternfly/components/FormControl/form-control.css";
import PFSelect from "@patternfly/patternfly/components/Select/select.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-search-select")
export class SearchSelect<T> extends AKElement {
    @property()
    query?: string;

    @property({ attribute: false })
    objects: T[] = [];

    @property({ attribute: false })
    selectedObject?: T;

    @property()
    name?: string;

    @property({ type: Boolean })
    open = false;

    @property({ type: Boolean })
    blankable = false;

    @property()
    placeholder: string = t`Select an object.`;

    static get styles(): CSSResult[] {
        return [PFBase, PFForm, PFFormControl, PFSelect, AKGlobal];
    }

    @property({ attribute: false })
    fetchObjects!: (query?: string) => Promise<T[]>;

    @property({ attribute: false })
    renderElement!: (element: T) => string;

    @property({ attribute: false })
    value!: (element: T | undefined) => unknown;

    @property({ attribute: false })
    selected!: (element: T) => boolean;

    firstUpdated(): void {
        this.fetchObjects(this.query).then((objects) => {
            this.objects = objects;
            this.objects.forEach((obj) => {
                if (this.selected(obj)) {
                    this.selectedObject = obj;
                }
            });
        });
    }

    menuId: string;

    constructor() {
        super();
        this.menuId = btoa(Math.random().toString()).substring(10, 15);
    }

    disconnectedCallback(): void {
        super.disconnectedCallback();
        document.querySelectorAll(`#${this.menuId}`).forEach((e) => e.remove());
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
        const pos = this.getBoundingClientRect();
        render(
            html`<div
                class="pf-c-dropdown pf-m-expanded"
                ?hidden=${!this.open}
                id="${this.menuId}"
                style="position: fixed; inset: 0px auto auto 0px; z-index: 9999; transform: translate(${pos.x}px, ${pos.y +
                this.offsetHeight}px); width: ${pos.width}px;"
            >
                <ul class="pf-c-dropdown__menu pf-m-static" role="listbox">
                    ${this.blankable
                        ? html`
                              <li role="presentation">
                                  <button
                                      class="pf-c-dropdown__menu-item"
                                      role="option"
                                      @click=${() => {
                                          this.selectedObject = undefined;
                                          this.open = false;
                                      }}
                                  >
                                      ---------
                                  </button>
                              </li>
                          `
                        : html``}
                    ${this.objects.map((obj) => {
                        return html`
                            <li role="presentation">
                                <button
                                    class="pf-c-dropdown__menu-item"
                                    role="option"
                                    @click=${() => {
                                        this.selectedObject = obj;
                                        this.open = false;
                                    }}
                                >
                                    ${this.renderElement(obj)}
                                </button>
                            </li>
                        `;
                    })}
                </ul>
            </div>`,
            document.body,
            { host: this },
        );
    }

    render(): TemplateResult {
        this.renderMenu();
        return html`<div class="pf-c-select">
            <div class="pf-c-select__toggle pf-m-typeahead">
                <div class="pf-c-select__toggle-wrapper">
                    <input
                        class="pf-c-form-control pf-c-select__toggle-typeahead"
                        type="text"
                        placeholder=${this.placeholder}
                        @input=${(ev: InputEvent) => {
                            this.query = (ev.target as HTMLInputElement).value;
                            this.firstUpdated();
                        }}
                        @focus=${() => {
                            this.open = true;
                            this.renderMenu();
                        }}
                        @blur=${() => {
                            setTimeout(() => {
                                this.open = false;
                                this.renderMenu();
                            }, 200);
                        }}
                        .value=${this.selectedObject ? this.renderElement(this.selectedObject) : ""}
                    />
                </div>
            </div>
        </div>`;
    }
}
