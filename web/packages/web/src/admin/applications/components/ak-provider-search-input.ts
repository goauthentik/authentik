import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { groupBy } from "@goauthentik/common/utils";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/forms/SearchSelect";

import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import { Provider, ProvidersAllListRequest, ProvidersApi } from "@goauthentik/api";

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

    @property({ type: String })
    name!: string;

    @property({ type: String })
    label = "";

    @property({ type: Number })
    value?: number;

    @property({ type: Boolean })
    required = false;

    @property({ type: Boolean })
    blankable = false;

    @property({ type: String })
    help = "";

    constructor() {
        super();
        this.selected = this.selected.bind(this);
    }

    selected(item: Provider) {
        return this.value !== undefined && this.value === item.pk;
    }

    render() {
        return html` <ak-form-element-horizontal label=${this.label} name=${this.name}>
            <ak-search-select
                .selected=${this.selected}
                .fetchObjects=${fetch}
                .renderElement=${renderElement}
                .value=${renderValue}
                .groupBy=${doGroupBy}
                ?blankable=${this.blankable}
            >
            </ak-search-select>
            ${this.help ? html`<p class="pf-c-form__helper-text">${this.help}</p>` : nothing}
        </ak-form-element-horizontal>`;
    }
}
