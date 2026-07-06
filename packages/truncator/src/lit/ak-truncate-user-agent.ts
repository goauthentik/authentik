import { truncateUserAgent } from "../user-agent.js";
import { AKTruncateBase, createTruncatorFC } from "./ak-truncate-base.js";

import { customElement } from "lit/decorators.js";

@customElement("ak-truncate-user-agent")
export class AKTruncateUserAgent extends AKTruncateBase {
    protected truncator = truncateUserAgent;
}

export const TruncateUserAgent = createTruncatorFC(AKTruncateUserAgent);

declare global {
    interface HTMLElementTagNameMap {
        "ak-truncate-user-agent": AKTruncateUserAgent;
    }
}
