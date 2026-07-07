/**
 * @file Email truncation — shrink the local part first, then the domain.
 */

import { shrinkHost } from "./internal/host.js";
import { endEllipsis, middleEllipsis, type TruncateOptions } from "./internal/primitives.js";
import { characterMeasurer } from "./measurer.js";

/**
 * Truncate an email address. The local part is middle-ellipsized first while the
 * `@domain` is kept intact; if that still doesn't fit, the domain is shrunk via
 * {@link shrinkHost}.
 *
 * @param input The email address to truncate.
 */
export function truncateEmail(input: string, options: TruncateOptions): string {
    const measure = options.measure ?? characterMeasurer;
    const ellipsis = options.ellipsis ?? "…";

    if (measure(input) <= options.maxWidth) {
        return input;
    }

    const at = input.lastIndexOf("@");

    if (at === -1) {
        return middleEllipsis(input, options);
    }

    const local = input.slice(0, at);
    const domain = input.slice(at + 1);

    // Shrink only the local part, keeping "@domain" intact...
    const suffix = "@" + domain;
    const localBudget = options.maxWidth - measure(suffix);

    if (localBudget >= measure(ellipsis)) {
        const candidate = middleEllipsis(local, { ...options, maxWidth: localBudget }) + suffix;

        if (measure(candidate) <= options.maxWidth) return candidate;
    }

    // Then, shrink the domain too. Keep a minimal local head,
    // ellipsize the domain, then hard-cut the whole thing to guarantee the budget.
    const domainBudget = Math.max(measure(ellipsis), options.maxWidth - measure("x@"));
    const shrunkDomain = shrinkHost(domain, { ...options, maxWidth: domainBudget });

    return endEllipsis(local.charAt(0) + "…@" + shrunkDomain, options);
}
