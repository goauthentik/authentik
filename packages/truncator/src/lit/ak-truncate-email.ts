import { truncateEmail } from "../email.js";
import { AKTruncateBase, createTruncatorFC } from "./ak-truncate-base.js";

import { customElement } from "lit/decorators.js";

@customElement("ak-truncate-email")
export class AKTruncateEmail extends AKTruncateBase {
    protected truncator = truncateEmail;
}

export const TruncateEmail = createTruncatorFC(AKTruncateEmail);

declare global {
    interface HTMLElementTagNameMap {
        "ak-truncate-email": AKTruncateEmail;
    }
}
