import { truncateURL } from "../url.js";
import { AKTruncateBase, createTruncatorFC } from "./ak-truncate-base.js";

import { customElement } from "lit/decorators.js";

@customElement("ak-truncate-url")
export class AKTruncateURL extends AKTruncateBase {
    protected truncator = truncateURL;
}

export const TruncateURL = createTruncatorFC(AKTruncateURL);

declare global {
    interface HTMLElementTagNameMap {
        "ak-truncate-url": AKTruncateURL;
    }
}
