import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { SearchSelect } from "#elements/forms/SearchSelect/index";
import { CustomListenerElement } from "#elements/utils/eventEmitter";

import {
    CertificateKeyPair,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
} from "@goauthentik/api";

import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

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
    public name?: string | null;

    @property({ type: String })
    public label?: string | undefined;

    @property({ type: String })
    public placeholder?: string | undefined;

    /**
     * Set to `true` to allow certificates without private key to show up. When set to `false`,
     * a private key is not required to be set.
     * @attr
     */
    @property({ type: Boolean, attribute: "nokey" })
    public noKey = false;

    /**
     * Set this to true if, should there be only one certificate available, you want the system to
     * use it by default.
     *
     * @attr
     */
    @property({ type: Boolean, attribute: "singleton" })
    public singleton = false;

    /**
     * @todo Document this.
     */
    public selectedKeypair?: CertificateKeyPair;

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

    handleSearchUpdate = (ev: CustomEvent) => {
        ev.stopPropagation();
        this.selectedKeypair = ev.detail.value;
        this.dispatchEvent(new InputEvent("input", { bubbles: true, composed: true }));
    };

    fetchObjects = async (query?: string): Promise<CertificateKeyPair[]> => {
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
    };

    selected = (item: CertificateKeyPair, items: CertificateKeyPair[]) => {
        return (
            (this.singleton && !this.certificate && items.length === 1) ||
            (!!this.certificate && this.certificate === item.pk)
        );
    };

    render() {
        return html`
            <ak-search-select
                name=${ifDefined(this.name ?? undefined)}
                label=${ifDefined(this.label ?? undefined)}
                placeholder=${ifDefined(this.placeholder)}
                .fetchObjects=${this.fetchObjects}
                .renderElement=${renderElement}
                .value=${renderValue}
                .selected=${this.selected}
                @ak-change=${this.handleSearchUpdate}
                blankable
            >
            </ak-search-select>
        `;
    }
}

export default AkCryptoCertificateSearch;

declare global {
    interface HTMLElementTagNameMap {
        "ak-crypto-certificate-search": AkCryptoCertificateSearch;
    }
}
