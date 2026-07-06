/**
 * @file User-agent truncation — parse to a compact "Browser N · OS" summary.
 */

import { endEllipsis, type TruncateOptions } from "./internal/primitives.js";

/**
 * Browser matchers, ordered so Chromium-derived browsers (Edge, Opera, Samsung)
 * are detected before Chrome, and Safari (which relies on the absence of the
 * others) is last.
 */
const BROWSER_Pairs: Array<[name: string, re: RegExp]> = [
    ["Edge", /Edg(?:e|A|iOS)?\/(\d+)/],
    ["Opera", /OPR\/(\d+)/],
    ["Samsung Internet", /SamsungBrowser\/(\d+)/],
    ["Chrome", /Chrome\/(\d+)/],
    ["Firefox", /Firefox\/(\d+)/],
    ["Safari", /Version\/(\d+)[.\d]*\s+.*Safari/],
];

const OS_PAIRS: Array<[name: string, re: RegExp]> = [
    ["Windows", /Windows NT [\d.]+/],
    ["macOS", /Mac OS X/],
    ["Android", /Android/],
    ["iOS", /iPhone|iPad|iPod/],
    ["Linux", /Linux/],
];

/**
 * Truncate a user-agent string by summarizing it to `"Browser N · OS"`, then
 * end-ellipsizing if the summary is still over budget. Unrecognized agents fall
 * back to end-ellipsizing the raw string.
 */
export function truncateUserAgent(input: string, options: TruncateOptions): string {
    let browser = "";
    for (const [name, re] of BROWSER_Pairs) {
        const match = input.match(re);

        if (match) {
            browser = match[1] ? `${name} ${match[1]}` : name;

            break;
        }
    }

    let os = "";

    for (const [name, re] of OS_PAIRS) {
        if (re.test(input)) {
            os = name;
            break;
        }
    }

    let summary: string;

    if (browser && os) {
        summary = `${browser} · ${os}`;
    } else if (browser) {
        summary = browser;
    } else if (os) {
        summary = os;
    } else {
        summary = input;
    }

    return endEllipsis(summary, options);
}
