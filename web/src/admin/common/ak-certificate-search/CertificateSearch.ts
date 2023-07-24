import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { property, query } from "lit/decorators.js";

import {
    CertificateKeyPair,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
} from "@goauthentik/api";

export function renderElement(item: CertificateKeyPair) {
    return item.name;
}

export function getValue(item: NonNullable<CertificateKeyPair>): string {
    return item?.pk;
}

/**
 * AkCertificateSearch
 *
 * A wrapper around SearchSelect that understands the basic semantics of querying Cryptographic
 * Certificates. This code eliminates the long blocks of unreadable invocation that were embedded in
 * many of our forms.
 *
 */

export abstract class CertificateSearch extends CustomListenerElement(AKElement) {
    /**
     * If set, this search will only show certificate-key pairs that have keys.
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "has-key" })
    hasKey = false;

    /**
     * The id of the current certificate
     *
     * @attr
     */
    @property({ type: String, attribute: "current-certificate" })
    currentCert: string | undefined;

    /**
     * If true, it is not valid to leave this search blank.
     *
     * @attr
     */
    @property({ type: Boolean })
    required?: boolean = false;

    @query("ak-search-select")
    search!: SearchSelect<CertificateKeyPair>;

    @property({ type: String })
    name: string | null | undefined;

    selectedCert?: CertificateKeyPair;

    get value() {
        return this.selectedCert ? getValue(this.selectedCert) : undefined;
    }

    constructor() {
        super();
        this.fetchObjects = this.fetchObjects.bind(this);
        this.selected = this.selected.bind(this);
        this.handleSearchUpdate = this.handleSearchUpdate.bind(this);
        this.addCustomListener("ak-change", this.handleSearchUpdate);
    }

    handleSearchUpdate(ev: CustomEvent) {
        ev.stopPropagation();
        this.selectedCert = ev.detail.value;
    }

    async fetchObjects(): Promise<CertificateKeyPair[]> {
        const args: CryptoCertificatekeypairsListRequest = {
            ordering: "name",
            includeDetails: false,
            ...(this.hasKey ? { hasKey: true } : {}),
        };
        const certificates = await new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsList(
            args,
        );
        return certificates.results;
    }

    abstract selected(item: CertificateKeyPair, items?: CertificateKeyPair[]): boolean;

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

    render() {
        return html`
            <ak-search-select
                .fetchObjects=${this.fetchObjects}
                .selected=${this.selected}
                .renderElement=${renderElement}
                .value=${getValue}
                ?blankable=${!this.required}
            >
            </ak-search-select>
        `;
    }
}

export default CertificateSearch;
