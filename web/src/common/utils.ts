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

export type GroupKeyCallback<T> = (item: T, index: number, array: T[]) => string;
export type GroupResult<T> = [groupKey: string, items: T[]];

export function groupBy<T>(items: T[], callback: GroupKeyCallback<T>): Array<GroupResult<T>> {
    const map = new Map<string, T[]>();

    items.forEach((item, index) => {
        const groupKey = callback(item, index, items);
        let tProviders = map.get(groupKey);

        if (!tProviders) {
            tProviders = [];

            map.set(groupKey, tProviders);
        }

        tProviders.push(item);
    });

    return Array.from(map).sort(([a], [b]) => a.localeCompare(b));
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

    crypto.getRandomValues(array);

    for (let index = 0; index < len; index++) {
        chars.push(charset[Math.floor(charset.length * (array[index] / Math.pow(2, 8)))]);
    }

    return chars.join("");
}
