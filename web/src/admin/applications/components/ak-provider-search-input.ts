import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";
import { groupBy } from "#common/utils";

import { AKElement } from "#elements/Base";

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
    protected override createRenderRoot() {
        return this;
    }

    @property({ type: String })
    public name!: string;

    @property({ type: String })
    public label = "";

    @property({ type: Number })
    public value?: number;

    @property({ type: Boolean })
    public required = false;

    @property({ type: Boolean })
    public blankable = false;

    @property({ type: String })
    public help = "";

    public constructor() {
        super();
        this.selected = this.selected.bind(this);
    }

    selected(item: Provider) {
        return this.value !== undefined && this.value === item.pk;
    }

    public override render() {
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-provider-search-input": AkProviderInput;
    }
}
