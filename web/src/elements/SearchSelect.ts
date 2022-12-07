import { AKElement } from "@goauthentik/elements/Base";

import { t } from "@lingui/macro";

import { css, CSSResult, html, TemplateResult } from "lit";
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
        return [PFBase, PFForm, PFFormControl, PFSelect, AKGlobal, css`.pf-c-select__menu { max-height: 18em; overflow-y: auto; -ms-overflow-style: none; scrollbar-width: none; } .pf-c-select__menu::-webkit-scrollbar { display: none; }`];
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

    render(): TemplateResult {
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
                        }}
                        @blur=${() => {
                            setTimeout(() => {
                                this.open = false;
                            }, 200);
                        }}
                        .value=${this.selectedObject ? this.renderElement(this.selectedObject) : ""}
                    />
                </div>
            </div>

            <ul class="pf-c-select__menu" role="listbox" ?hidden="${!this.open}">
                ${this.blankable
                    ? html`
                          <li role="presentation">
                              <button
                                  class="pf-c-select__menu-item"
                                  role="option"
                                  @click=${() => {
                                      this.selectedObject = undefined;
                                      this.open = false;
                                      console.log("click");
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
                                class="pf-c-select__menu-item"
                                role="option"
                                @click=${() => {
                                    this.selectedObject = obj;
                                    this.open = false;
                                    console.log("click");
                                }}
                            >
                                ${this.renderElement(obj)}
                            </button>
                        </li>
                    `;
                })}
            </ul>
        </div>`;
    }
}
