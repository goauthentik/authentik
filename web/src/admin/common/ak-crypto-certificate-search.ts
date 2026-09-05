import "#elements/forms/SearchSelect/index";

import { aki } from "#common/api/client";

import { AKElement } from "#elements/Base";
import { ISearchSelect } from "#elements/forms/SearchSelect/ak-search-select";
import { SlottedTemplateResult } from "#elements/types";
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

const renderValue = (item: CertificateKeyPair | null) => item?.pk;

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
    certificate?: string | null;

    @query("ak-search-select")
    search!: ISearchSelect<CertificateKeyPair>;

    @property({ type: String })
    public name?: string | null;

    @property({ type: String })
    public label: string | null = msg("Certificate");

    @property({ type: String })
    public placeholder: string | null = msg("Select a certificate...");

    /**
     * Set to `true` to allow certificates without private key to be selected. When set to `false`,
     * keypairs without a private key are listed but cannot be chosen.
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
     * When allowedKeyTypes is set, only certificates or keypairs with matching
     * key algorithms can be selected. Others are listed but cannot be chosen.
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

    /**
     * Why this keypair cannot be used for the field it is being offered in, or `null` if it can.
     *
     * Unusable keypairs used to be filtered out of the query entirely, which left no trace of them
     * in the menu — a certificate simply wasn't there, with no hint as to why. They are listed
     * instead, sorted last and inert, carrying the reason as their description.
     */
    #unusableReason = (item: CertificateKeyPair): string | null => {
        if (!this.noKey && !item.privateKeyAvailable) {
            return msg("This certificate is not a valid option here: it has no private key.", {
                id: "crypto.certificate-search.missing-private-key.description",
            });
        }

        if (
            this.allowedKeyTypes?.length &&
            (!item.keyType || !this.allowedKeyTypes.includes(item.keyType))
        ) {
            return msg("This certificate is not a valid option here: unsupported key type.", {
                id: "crypto.certificate-search.unsupported-key-type.description",
            });
        }

        return null;
    };

    fetchObjects = async (query?: string): Promise<CertificateKeyPair[]> => {
        const args: CryptoCertificatekeypairsListRequest = {
            ordering: "name",
        };
        if (query !== undefined) {
            args.search = query;
        }

        const restrictions: CryptoCertificatekeypairsListRequest = {};
        if (!this.noKey) {
            restrictions.hasKey = true;
        }
        if (this.allowedKeyTypes?.length) {
            restrictions.keyType = this.allowedKeyTypes;
        }

        const api = aki(CryptoApi);

        if (Object.keys(restrictions).length === 0) {
            const { results } = await api.cryptoCertificatekeypairsList(args);
            return results;
        }

        // The API only returns one page of results, so ask it for the usable keypairs directly.
        // Otherwise, a page full of unusable ones could push the usable ones out of the list.
        const [{ results: usable }, { results: all }] = await Promise.all([
            api.cryptoCertificatekeypairsList({ ...args, ...restrictions }),
            api.cryptoCertificatekeypairsList(args),
        ]);

        const unusable = all.filter((item) => this.#unusableReason(item) !== null);

        return [...usable, ...unusable];
    };

    optionDisabled = (item: CertificateKeyPair): boolean => this.#unusableReason(item) !== null;

    renderDescription = (item: CertificateKeyPair): SlottedTemplateResult =>
        this.#unusableReason(item);

    selected = (item: CertificateKeyPair, items: CertificateKeyPair[]) => {
        if (this.certificate) {
            return this.certificate === item.pk;
        }

        if (!this.singleton) {
            return false;
        }

        // Only a lone *selectable* certificate can stand in as the default.
        const usable = items.filter((candidate) => !this.#unusableReason(candidate));

        return usable.length === 1 && usable[0].pk === item.pk;
    };

    render() {
        return html`
            <ak-search-select
                name=${ifPresent(this.name)}
                label=${ifPresent(this.label)}
                placeholder=${ifPresent(this.placeholder)}
                .fetchObjects=${this.fetchObjects}
                .renderElement=${renderElement}
                .renderDescription=${this.renderDescription}
                .optionDisabled=${this.optionDisabled}
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
