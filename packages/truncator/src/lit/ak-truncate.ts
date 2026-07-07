import { truncateString } from "../string.js";
import { AKTruncateBase, createTruncatorFC } from "./ak-truncate-base.js";

import { customElement } from "lit/decorators.js";

@customElement("ak-truncate")
export class AKTruncate extends AKTruncateBase {
    protected truncator = truncateString;
}

export const Truncate = createTruncatorFC(AKTruncate);

declare global {
    interface HTMLElementTagNameMap {
        "ak-truncate": AKTruncate;
    }
}
