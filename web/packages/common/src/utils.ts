import { SentryIgnoredError } from "@goauthentik/common/errors.js";

import { CSSResult, css } from "lit";

export function getCookie(name: string): string {
    let cookieValue = "";
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === `${name}=`) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

export function convertToSlug(text: string): string {
    return text
        .toLowerCase()
        .replace(/ /g, "-")
        .replace(/[^\w-]+/g, "");
}

const WORD_COUNT_TRUNCATION_DEFAULT = 10;
/**
 * Truncate a string based on maximum word count
 */
export function truncateWords(input: string, length = WORD_COUNT_TRUNCATION_DEFAULT): string {
    const words = (input ?? "").trim().split(" ");
    const ellipsis = words.length > length ? "..." : "";
    return words.slice(0, length).join(" ") + ellipsis;
}

const CHAR_COUNT_TRUNCATION_DEFAULT = 10;
/**
 * Truncate a string based on character count
 */
export function truncate(string: string, length = CHAR_COUNT_TRUNCATION_DEFAULT): string {
    return string.length > length ? `${string.substring(0, length)}...` : string;
}

export function camelToSnake(key: string): string {
    const result = key.replace(/([A-Z])/g, " $1");
    return result.split(" ").join("_").toLowerCase();
}

const capitalize = (key: string) => (key.length === 0 ? "" : key[0].toUpperCase() + key.slice(1));

export function snakeToCamel(key: string) {
    const [start, ...rest] = key.split("_");
    return [start, ...rest.map(capitalize)].join("");
}

export function groupBy<T>(objects: T[], callback: (obj: T) => string): Array<[string, T[]]> {
    const m = new Map<string, T[]>();
    objects.forEach((obj) => {
        const group = callback(obj);
        if (!m.has(group)) {
            m.set(group, []);
        }
        const tProviders = m.get(group) || [];
        tProviders.push(obj);
    });
    return Array.from(m).sort();
}

export function first<T>(...args: Array<T | undefined | null>): T {
    for (let index = 0; index < args.length; index++) {
        const element = args[index];
        if (element !== undefined && element !== null) {
            return element;
        }
    }
    throw new SentryIgnoredError(`No compatible arg given: ${args}`);
}

// Taken from python's string module
export const ascii_lowercase = "abcdefghijklmnopqrstuvwxyz";
export const ascii_uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
export const ascii_letters = ascii_lowercase + ascii_uppercase;
export const digits = "0123456789";
export const hexdigits = `${digits}abcdefABCDEF}`;
export const octdigits = "01234567";
export const punctuation = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~";

const BYTE_SIZE = 256;

export function randomString(len: number, charset: string): string {
    const chars = [];
    const array = new Uint8Array(len);
    self.crypto.getRandomValues(array);
    for (let index = 0; index < len; index++) {
        chars.push(charset[Math.floor(charset.length * (array[index] / BYTE_SIZE))]);
    }
    return chars.join("");
}

const TIMEZONE_OFFSET = 60000; // milliseconds

export function dateTimeLocal(date: Date): string {
    // So for some reason, the datetime-local input field requires ISO Datetime as value
    // But the standard javascript date.toISOString() returns everything with seconds and
    // milliseconds, which the input field doesn't like (on chrome, on firefox its fine)
    // On chrome, setting .valueAsNumber works, but that causes an error on firefox, so go
    // figure.
    // Additionally, toISOString always returns the date without timezone, which we would like
    // to include for better usability
    const tzOffset = new Date().getTimezoneOffset() * TIMEZONE_OFFSET;
    const localISOTime = new Date(date.getTime() - tzOffset).toISOString().slice(0, -1);
    const parts = localISOTime.split(":");
    return `${parts[0]}:${parts[1]}`;
}

export function dateToUTC(date: Date): Date {
    // Sigh...so our API is UTC/can take TZ info in the ISO format as it should.
    // datetime-local fields (which is almost the only date-time input we use)
    // can return its value as a UTC timestamp...however the generated API client
    // _requires_ a Date object, only to then convert it to an ISO string anyways
    // JS Dates don't include timezone info in the ISO string, so that just sends
    // the local time as UTC...which is wrong
    // Instead we have to do this, convert the given date to a UTC timestamp,
    // then subtract the timezone offset to create an "invalid" date (correct time&date)
    // but it still "thinks" it's in local TZ
    const timestamp = date.getTime();
    const offset = -1 * (new Date().getTimezoneOffset() * TIMEZONE_OFFSET);
    return new Date(timestamp - offset);
}

// Lit is extremely well-typed with regard to CSS, and Storybook's `build` does not currently have a
// coherent way of importing CSS-as-text into CSSStyleSheet. It works well when Storybook is running
// in `dev,` but in `build` it fails. Storied components will have to map their textual CSS imports
// using the function below.
type AdaptableStylesheet = Readonly<string | CSSResult | CSSStyleSheet>;
type AdaptedStylesheets = CSSStyleSheet | CSSStyleSheet[];

const isCSSResult = (v: unknown): v is CSSResult =>
    v instanceof CSSResult && v.styleSheet !== undefined;

// prettier-ignore
export const _adaptCSS = (sheet: AdaptableStylesheet): CSSStyleSheet =>
    (typeof sheet === "string" ? css([sheet] as unknown as TemplateStringsArray, []).styleSheet
        : isCSSResult(sheet) ? sheet.styleSheet
        : sheet) as CSSStyleSheet;

// Overloaded function definitions inform consumers that if you pass it an array, expect an array in
// return; if you pass it a scaler, expect a scalar in return.

export function adaptCSS(sheet: AdaptableStylesheet): CSSStyleSheet;
export function adaptCSS(sheet: AdaptableStylesheet[]): CSSStyleSheet[];
export function adaptCSS(sheet: AdaptableStylesheet | AdaptableStylesheet[]): AdaptedStylesheets {
    return Array.isArray(sheet) ? sheet.map(_adaptCSS) : _adaptCSS(sheet);
}

const SECONDS_IN_A_MINUTE = 60;
const MINUTES_IN_AN_HOUR = 60;
const HOURS_IN_A_DAY = 24;
const DAYS_IN_A_YEAR = 365;
const MONTHS_IN_A_YEAR = 12;

const MILLISECONDS_IN_A_SECOND = 1000;
const MILLISECONDS_IN_A_MINUTE = MILLISECONDS_IN_A_SECOND * SECONDS_IN_A_MINUTE;
const MILLISECONDS_IN_AN_HOUR = MILLISECONDS_IN_A_MINUTE * MINUTES_IN_AN_HOUR;
const MILLISECONDS_IN_A_DAY = MILLISECONDS_IN_AN_HOUR * HOURS_IN_A_DAY;
const MILLISECONDS_IN_A_YEAR = MILLISECONDS_IN_A_DAY * DAYS_IN_A_YEAR;
const MILLISECONDS_IN_A_MONTH = MILLISECONDS_IN_A_YEAR / MONTHS_IN_A_YEAR;

const _timeUnits = new Map<Intl.RelativeTimeFormatUnit, number>([
    ["year", MILLISECONDS_IN_A_YEAR],
    ["month", MILLISECONDS_IN_A_MONTH],
    ["day", MILLISECONDS_IN_A_DAY],
    ["hour", MILLISECONDS_IN_AN_HOUR],
    ["minute", MILLISECONDS_IN_A_MINUTE],
    ["second", MILLISECONDS_IN_A_SECOND],
]);

export function getRelativeTime(d1: Date, d2: Date = new Date()): string {
    const rtf = new Intl.RelativeTimeFormat("default", { numeric: "auto" });
    const elapsed = d1.getTime() - d2.getTime();

    // "Math.abs" accounts for both "past" & "future" scenarios
    for (const [key, value] of _timeUnits) {
        if (Math.abs(elapsed) > value || key === "second") {
            return rtf.format(Math.round(elapsed / value), key);
        }
    }
    return rtf.format(Math.round(elapsed / MILLISECONDS_IN_A_SECOND), "second");
}
