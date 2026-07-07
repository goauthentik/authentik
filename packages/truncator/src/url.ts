/**
 * @file URL truncation. A measure-gated pipeline that strips low-value URL
 * chrome (protocol, www, port), ellipsizes machine-unfriendly query params and
 * path segments, then shrinks the host and hard-cuts as a last resort.
 */

import { shrinkHost } from "./internal/host.js";
import { endEllipsis, reducePipeline, type TruncateOptions } from "./internal/primitives.js";

const MARK = "…";

/**
 * Does every dash/dot/underscore-delimited part of `input` look like a word,
 * acronym, or number (i.e. human-readable rather than an opaque token)?
 */
function isWordedPart(input: string): boolean {
    const wordRe = /^(([a-z]*?[aeiouy][a-z]*?)|(\d*)|q)$/i;
    const acronymRe = /^([a-z]{2,5}|[A-Z]{2,5})$/;

    for (const part of input.split(/-|\.|,|\+|_|%20/)) {
        if (!wordRe.test(part) && !acronymRe.test(part)) {
            return false;
        }
    }

    return true;
}

/**
 * Collapse runs of adjacent ellipsized segments joined by `delimiter` down to one.
 */
function collapseAdjacent(input: string, delimiter: string): string {
    const triple = new RegExp(`\\${delimiter}${MARK}\\${delimiter}${MARK}\\${delimiter}`, "g");
    const leading = new RegExp(`${MARK}\\${delimiter}${MARK}\\${delimiter}`, "g");
    const trailing = new RegExp(`\\${delimiter}${MARK}\\${delimiter}${MARK}`, "g");

    let result = input;
    let prev;

    do {
        prev = result;
        result = result
            .replace(triple, `${delimiter}${MARK}${delimiter}`)
            .replace(leading, `${MARK}${delimiter}`)
            .replace(trailing, `${delimiter}${MARK}`);
    } while (result !== prev);

    return result;
}

type URLTransformer = (url: string, opts: TruncateOptions) => string;

const stripProtocol: URLTransformer = (url) => {
    return url.replace(/^https?:\/?\/?/i, "");
};

const stripWWW: URLTransformer = (url) => {
    return url.replace(/^www\./, "");
};

const stripPort: URLTransformer = (url) => {
    const parts = url.split("/");
    const host = parts[0] ?? "";
    parts[0] = host.split(":")[0] ?? host;

    return parts.join("/");
};

const ellipsizeQuery: URLTransformer = (url) => {
    const q = url.indexOf("?");

    if (q < 0) {
        return url;
    }

    const before = url.slice(0, q);
    let query = url.slice(q + 1);

    const hashAt = query.indexOf("#");
    const hash = hashAt > -1 ? query.slice(hashAt) : "";

    if (hashAt > -1) {
        query = query.slice(0, hashAt);
    }

    const parts = query.split("&").map((pair) => {
        const [key, val, ...rest] = pair.split("=");

        if (rest.length || val === undefined) return pair;

        const keyOk = isWordedPart(key ?? "");
        const valOk = isWordedPart(val);

        if (!keyOk && !valOk) return MARK;
        if (!keyOk) return `${MARK}=${val}`;
        if (!valOk) return `${key}=${MARK}`;

        return pair;
    });

    return before + "?" + collapseAdjacent(parts.join("&"), "&") + hash;
};

const ellipsizePath: URLTransformer = (url) => {
    const slash = url.indexOf("/");

    if (slash < 0) {
        return url;
    }

    const before = url.slice(0, slash);
    let after = url.slice(slash + 1);

    const q = after.indexOf("?");
    const h = after.indexOf("#");
    let cut = -1;

    if (q > -1 && h > -1) {
        cut = Math.min(q, h);
    } else if (q > -1) {
        cut = q;
    } else if (h > -1) {
        cut = h;
    }

    const suffix = cut > -1 ? after.slice(cut) : "";

    if (cut > -1) {
        after = after.slice(0, cut);
    }

    const parts = after.split("/").map((part) => {
        return isWordedPart(part) ? part : MARK;
    });

    return before + "/" + collapseAdjacent(parts.join("/"), "/") + suffix;
};

/**
 * Shrink the host (subdomains before domain+TLD) to whatever budget remains
 * after the path.
 */
const shrinkURLHost: URLTransformer = (url, opts) => {
    const slash = url.indexOf("/");
    const host = slash < 0 ? url : url.slice(0, slash);
    const rest = slash < 0 ? "" : url.slice(slash);

    const shrunk = shrinkHost(host, {
        ...opts,
        maxWidth: Math.max(1, opts.maxWidth - rest.length),
    });

    return shrunk + rest;
};

/**
 * Truncate a URL, keeping the human-meaningful host and path while ellipsizing
 * opaque query params and path segments.
 */
export function truncateURL(url: string, options: TruncateOptions): string {
    return reducePipeline(url, options, [
        stripProtocol,
        stripWWW,
        stripPort,
        ellipsizeQuery,
        ellipsizePath,
        shrinkURLHost,
        (value, $options) => endEllipsis(value, $options),
    ]);
}
