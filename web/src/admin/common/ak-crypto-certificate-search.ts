import "#elements/forms/SearchSelect/index";

import { DEFAULT_CONFIG } from "#common/api/config";

import { AKElement } from "#elements/Base";
import { SearchSelect } from "#elements/forms/SearchSelect/index";
import { ifPresent } from "#elements/utils/attributes";
import { CustomListenerElement } from "#elements/utils/eventEmitter";

import {
    CertificateKeyPair,
    CryptoApi,
    CryptoCertificatekeypairsListRequest,
    KeyTypeEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, query } from "lit/decorators.js";

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
    public label: string | null = msg("Certificate");

    @property({ type: String })
    public placeholder: string | null = msg("Select a certificate...");

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
     * Set to `true` to include certificate details (fingerprints, expiry, certificate subject, key type)
     * in the API response.
     * Each returned certificate's PEM data must be parsed using cryptography library,
     * public keys extracted, and hashes computed. With large result sets, this can add a lot of time
     * to responses.
     * Only enable when you actually need the detailed fields displayed in the UI.
     * For simple certificate selection dropdowns, leave this as `false` (default).
     * @attr
     */
    @property({ type: Boolean, attribute: "include-details" })
    public includeDetails = false;

    /**
     * When allowedKeyTypes is set, only certificates or keypairs with matching
     * key algorithms will be shown. Since certificates must be parsed to
     * extract algorithm details, an instance with many certificates may experience
     * long delays and server performance slowdowns. Avoid setting this field whenever possible.
     * @attr
     * @example [KeyTypeEnum.Rsa, KeyTypeEnum.Ec]
     */
    @property({ type: Array, attribute: "allowed-key-types" })
    public allowedKeyTypes?: KeyTypeEnum[];

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
            includeDetails: this.includeDetails,
        };
        if (query !== undefined) {
            args.search = query;
        }
        if (this.allowedKeyTypes?.length) {
            args.keyType = this.allowedKeyTypes;
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
                name=${ifPresent(this.name)}
                label=${ifPresent(this.label)}
                placeholder=${ifPresent(this.placeholder)}
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
