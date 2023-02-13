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

export function randomString(len: number): string {
    const arr = new Uint8Array(len / 2);
    window.crypto.getRandomValues(arr);
    return hexEncode(arr);
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
