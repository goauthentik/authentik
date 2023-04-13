import { SentryIgnoredError } from "@goauthentik/common/errors";

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

export function convertToTitle(text: string): string {
    return text.replace(/\w\S*/g, function (txt) {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
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

export function hexEncode(buf: Uint8Array): string {
    return Array.from(buf)
        .map(function (x) {
            return ("0" + x.toString(16)).substr(-2);
        })
        .join("");
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

export function dateTimeLocal(date: Date): string {
    // So for some reason, the datetime-local input field requires ISO Datetime as value
    // But the standard javascript date.toISOString() returns everything with seconds and
    // milliseconds, which the input field doesn't like (on chrome, on firefox its fine)
    // On chrome, setting .valueAsNumber works, but that causes an error on firefox, so go
    // figure.
    // Additionally, toISOString always returns the date without timezone, which we would like
    // to include for better usability
    const tzOffset = new Date().getTimezoneOffset() * 60000; //offset in milliseconds
    const localISOTime = new Date(date.getTime() - tzOffset).toISOString().slice(0, -1);
    const parts = localISOTime.split(":");
    return `${parts[0]}:${parts[1]}`;
}
