import { customElement } from "lit/decorators.js";

import { CertificateKeyPair } from "@goauthentik/api";

import { CertificateSearch } from "./CertificateSearch";

/**
 * CertificateSearch
 *
 * A wrapper around SearchSelect that understands the basic semantics of querying Cryptographic
 * Certificates. This code eliminates the long blocks of unreadable invocation that were embedded in
 * many of our forms.
 *
 */

@customElement("ak-certificate-search")
export class AkCertificateSearch extends CertificateSearch {
    selected(item: CertificateKeyPair): boolean {
        return this.currentCert === item.pk;
    }
}

export default AkCertificateSearch;
