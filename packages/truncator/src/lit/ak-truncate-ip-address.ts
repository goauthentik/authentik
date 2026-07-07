import { truncateIPAddress } from "../ip-address.js";
import { AKTruncateBase, createTruncatorFC } from "./ak-truncate-base.js";

import { customElement } from "lit/decorators.js";

@customElement("ak-truncate-ip-address")
export class AKTruncateIPAddress extends AKTruncateBase {
    protected truncator = truncateIPAddress;
}

export const TruncateIPAddress = createTruncatorFC(AKTruncateIPAddress);

declare global {
    interface HTMLElementTagNameMap {
        "ak-truncate-ip-address": AKTruncateIPAddress;
    }
}
