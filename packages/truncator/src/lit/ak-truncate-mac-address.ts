import { truncateMacAddress } from "../mac-address.js";
import { AKTruncateBase, createTruncatorFC } from "./ak-truncate-base.js";

import { customElement } from "lit/decorators.js";

@customElement("ak-truncate-mac-address")
export class AKTruncateMacAddress extends AKTruncateBase {
    protected truncator = truncateMacAddress;
}

export const TruncateMacAddress = createTruncatorFC(AKTruncateMacAddress);

declare global {
    interface HTMLElementTagNameMap {
        "ak-truncate-mac-address": AKTruncateMacAddress;
    }
}
