import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { AKElement } from "#elements/Base";

import { AKLabel } from "#components/ak-label";

import { IDGenerator } from "#packages/core/id";

import { Provider, ProvidersAllListRequest, ProvidersApi } from "@goauthentik/api";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

const renderElement = (item: Provider) => item.name;
const renderValue = (item: Provider | undefined) => item?.pk;
const doGroupBy = (items: Provider[]) => groupBy(items, (item) => item.verboseName);

async function fetch(query?: string) {
    const args: ProvidersAllListRequest = {
        ordering: "name",
    };
    if (query !== undefined) {
        args.search = query;
    }
    const items = await new ProvidersApi(DEFAULT_CONFIG).providersAllList(args);
    return items.results;
}

@customElement("ak-provider-search-input")
export class AkProviderInput extends AKElement {
    // Render into the lightDOM. This effectively erases the shadowDOM nature of this component, but
    // we're not actually using that and, for the meantime, we need the form handlers to be able to
    // find the children of this component.
    //
    // TODO: This abstraction is wrong; it's putting *more* layers in as a way of managing the
    // visual clutter and legibility issues of ak-form-elemental-horizontal and patternfly in
    // general.
    protected createRenderRoot() {
        return this;
    }

    //#region Properties

    @property({ type: String })
    name!: string;

    @property({ type: String })
    label: string | null = null;

    @property({ type: Number })
    value?: number;

    @property({ type: Boolean })
    required = false;

    @property({ type: Boolean })
    blankable = false;

    @property({ type: String })
    help: string | null = null;

    /**
     * A unique ID to associate with the input and label.
     * @property
     */
    @property({ type: String, reflect: false })
    public fieldID?: string = IDGenerator.elementID().toString();

    //#endregion

    #selected = (item: Provider) => {
        return typeof this.value === "number" && this.value === item.pk;
    };

    render() {
        return html` <ak-form-element-horizontal name=${this.name}>
            <div slot="label" class="pf-c-form__group-label">
                ${AKLabel({ htmlFor: this.fieldID, required: this.required }, this.label)}
            </div>

            <ak-search-select
                .fieldID=${this.fieldID}
                .selected=${this.#selected}
                .fetchObjects=${fetch}
                .renderElement=${renderElement}
                .value=${renderValue}
                .groupBy=${doGroupBy}
                ?blankable=${!!this.blankable}
            >
            </ak-search-select>
            ${this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing}
        </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-search-input": AkProviderInput;
    }
}
