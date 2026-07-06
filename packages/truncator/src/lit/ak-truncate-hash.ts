import { truncateHash } from "../hash.js";
import { AKTruncateBase, createTruncatorFC } from "./ak-truncate-base.js";

import { customElement } from "lit/decorators.js";

@customElement("ak-truncate-hash")
export class AKTruncateHash extends AKTruncateBase {
    protected truncator = truncateHash;
}

export const TruncateHash = createTruncatorFC(AKTruncateHash);

declare global {
    interface HTMLElementTagNameMap {
        "ak-truncate-hash": AKTruncateHash;
    }
}
