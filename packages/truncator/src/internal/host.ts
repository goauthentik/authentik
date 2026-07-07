/**
 * @file Hostname shrinking utilities.
 */

import { characterMeasurer } from "../measurer.js";
import { middleEllipsis, type TruncateOptions } from "./primitives.js";

/**
 * Shrink a hostname to fit, prioritizing the registrable domain + TLD over subdomains.
 * With 3+ labels the subdomains collapse to a single leading ellipsis before
 * domain+TLD are touched; otherwise the whole host is middle-ellipsized.
 */
export function shrinkHost(host: string, options: TruncateOptions): string {
    const measure = options.measure ?? characterMeasurer;
    const ellipsis = options.ellipsis ?? "…";

    if (measure(host) <= options.maxWidth) {
        return host;
    }

    const labels = host.split(".");

    if (labels.length >= 3) {
        const collapsed = ellipsis + "." + labels.slice(-2).join(".");

        if (measure(collapsed) <= options.maxWidth) {
            return collapsed;
        }
    }

    return middleEllipsis(host, options);
}
