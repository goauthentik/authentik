import { SentryIgnoredError } from "@goauthentik/common/sentry";

import { CSSResult, css } from "lit";

export function getCookie(name: string): string {
    let cookieValue = "";
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === name + "=") {
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

export function isSlug(text: string): boolean {
    const lowered = text.toLowerCase();
    const forbidden = /([^\w-]|\s)/.test(lowered);
    return lowered === text && !forbidden;
}

/**
 * Truncate a string based on maximum word count
 */
export function truncateWords(string: string, length = 10): string {
    string = string || "";
    const array = string.trim().split(" ");
    const ellipsis = array.length > length ? "..." : "";

    return array.slice(0, length).join(" ") + ellipsis;
}

/**
 * Truncate a string based on character count
 */
export function truncate(string: string, length = 10): string {
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
export const hexdigits = digits + "abcdef" + "ABCDEF";
export const octdigits = "01234567";
export const punctuation = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~";

export function randomString(len: number, charset: string): string {
    const chars = [];
    const array = new Uint8Array(len);
    self.crypto.getRandomValues(array);
    for (let index = 0; index < len; index++) {
        chars.push(charset[Math.floor(charset.length * (array[index] / Math.pow(2, 8)))]);
    }
    return chars.join("");
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
