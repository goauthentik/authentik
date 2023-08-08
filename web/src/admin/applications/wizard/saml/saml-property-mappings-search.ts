import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { property, query } from "lit/decorators.js";

import {
    PropertymappingsApi,
    PropertymappingsSamlListRequest,
    SAMLPropertyMapping,
} from "@goauthentik/api";

async function fetchObjects(query?: string): Promise<SAMLPropertyMapping[]> {
    const args: PropertymappingsSamlListRequest = {
        ordering: "saml_name",
    };
    if (query !== undefined) {
        args.search = query;
    }
    const items = await new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlList(args);
    return items.results;
}

function renderElement(item: SAMLPropertyMapping): string {
    return item.name;
}

function renderValue(item: SAMLPropertyMapping | undefined): string | undefined {
    return item?.pk;
}

/**
 * SAML Property Mapping Search
 *
 * @element ak-saml-property-mapping-search
 *
 * A wrapper around SearchSelect for the SAML Property Search. It's a unique search, but for the
 * purpose of the form all you need to know is that it is being searched and selected. Let's put the
 * how somewhere else.
 *
 */

@customElement("ak-saml-property-mapping-search")
export class SAMLPropertyMappingSearch extends CustomListenerElement(AKElement) {
    /**
     * The current property mapping known to the caller.
     *
     * @attr
     */
    @property({ type: String, reflect: true, attribute: "propertymapping" })
    propertyMapping?: string;

    @query("ak-search-select")
    search!: SearchSelect<SAMLPropertyMapping>;

    @property({ type: String })
    name: string | null | undefined;

    selectedPropertyMapping?: SAMLPropertyMapping;

    constructor() {
        super();
        this.selected = this.selected.bind(this);
        this.handleSearchUpdate = this.handleSearchUpdate.bind(this);
        this.addCustomListener("ak-change", this.handleSearchUpdate);
    }

    get value() {
        return this.selectedPropertyMapping ? renderValue(this.selectedPropertyMapping) : undefined;
    }

    connectedCallback() {
        super.connectedCallback();
        const horizontalContainer = this.closest("ak-form-element-horizontal[name]");
        if (!horizontalContainer) {
            throw new Error("This search can only be used in a named ak-form-element-horizontal");
        }
        const name = horizontalContainer.getAttribute("name");
        const myName = this.getAttribute("name");
        if (name !== null && name !== myName) {
            this.setAttribute("name", name);
        }
    }

    handleSearchUpdate(ev: CustomEvent) {
        ev.stopPropagation();
        this.selectedPropertyMapping = ev.detail.value;
        this.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
    }

    selected(item: SAMLPropertyMapping): boolean {
        return this.propertyMapping === item.pk;
    }

    render() {
        return html`
            <ak-search-select
                .fetchObjects=${fetchObjects}
                .renderElement=${renderElement}
                .value=${renderValue}
                .selected=${this.selected}
                blankable
            >
            </ak-search-select>
        `;
    }
}

export default SAMLPropertyMappingSearch;
