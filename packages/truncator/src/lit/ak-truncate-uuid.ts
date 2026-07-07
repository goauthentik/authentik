import { truncateUUID } from "../uuid.js";
import { AKTruncateBase, createTruncatorFC } from "./ak-truncate-base.js";

import { customElement } from "lit/decorators.js";

@customElement("ak-truncate-uuid")
export class AKTruncateUUID extends AKTruncateBase {
    protected truncator = truncateUUID;
}

export const TruncateUUID = createTruncatorFC(AKTruncateUUID);

declare global {
    interface HTMLElementTagNameMap {
        "ak-truncate-uuid": AKTruncateUUID;
    }
}
