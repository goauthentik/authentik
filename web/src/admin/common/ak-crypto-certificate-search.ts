import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { AKElement } from "@goauthentik/elements/Base";
import { SearchSelect } from "@goauthentik/elements/forms/SearchSelect";
import "@goauthentik/elements/forms/SearchSelect";
import { CustomListenerElement } from "@goauthentik/elements/utils/eventEmitter";

import { html } from "lit";
import { customElement } from "lit/decorators.js";
import { property, query } from "lit/decorators.js";

import {
    CertificateKeyPair,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
} from "@goauthentik/api";

const renderElement = (item: CertificateKeyPair): string => item.name;

const renderValue = (item: CertificateKeyPair | undefined): string | undefined => item?.pk;

/**
 * Cryptographic Certificate Search
 *
 * @element ak-crypto-certificate-search
 *
 * A wrapper around SearchSelect for the many searches of cryptographic key-pairs used throughout our
 * code base. This is another one of those "If it's not error-free, at least it's localized to one
 * place" issues.
 *
 */

@customElement("ak-crypto-certificate-search")
export class AkCryptoCertificateSearch extends CustomListenerElement(AKElement) {
    @property({ type: String, reflect: true })
    certificate?: string;

    @query("ak-search-select")
    search!: SearchSelect<CertificateKeyPair>;

    @property({ type: String })
    name: string | null | undefined;

    /**
     * Set to `true` if you want to find pairs that don't have a valid key. Of our 14 searches, 11
     * require the key, 3 do not (as of 2023-08-01).
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "nokey" })
    noKey = false;

    /**
     * Set this to true if, should there be only one certificate available, you want the system to
     * use it by default.
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "singleton" })
    singleton = false;

    selectedKeypair?: CertificateKeyPair;

    constructor() {
        super();
        this.selected = this.selected.bind(this);
        this.fetchObjects = this.fetchObjects.bind(this);
        this.handleSearchUpdate = this.handleSearchUpdate.bind(this);
        this.addCustomListener("ak-change", this.handleSearchUpdate);
    }

    get value() {
        return this.selectedKeypair ? renderValue(this.selectedKeypair) : null;
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
        this.selectedKeypair = ev.detail.value;
        this.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
    }

    async fetchObjects(query?: string): Promise<CertificateKeyPair[]> {
        const args: CryptoCertificatekeypairsListRequest = {
            ordering: "name",
            hasKey: !this.noKey,
            includeDetails: false,
        };
        if (query !== undefined) {
            args.search = query;
        }
        const certificates = await new CryptoApi(DEFAULT_CONFIG).cryptoCertificatekeypairsList(
            args,
        );
        return certificates.results;
    }

    selected(item: CertificateKeyPair, items: CertificateKeyPair[]) {
        return (
            (this.singleton && !this.certificate && items.length === 1) ||
            (!!this.certificate && this.certificate === item.pk)
        );
    }

    render() {
        return html`
            <ak-search-select
                .fetchObjects=${this.fetchObjects}
                .renderElement=${renderElement}
                .value=${renderValue}
                .selected=${this.selected}
                ?blankable=${true}
            >
            </ak-search-select>
        `;
    }
}

export default AkCryptoCertificateSearch;
