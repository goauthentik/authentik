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
export const hexdigits = digits + "abcdefABCDEF";
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

export function assertEveryPresent<T>(
    input: (T | null | undefined)[],
    errorMessage: string,
): asserts input is T[] {
    if (!Array.isArray(input)) {
        console.debug("Input is not an array", input);
        throw TypeError(errorMessage);
    }

    const index = input.findIndex((item) => item === null || typeof item === "undefined");
    if (index !== -1) {
        console.debug(`Item at index ${index} is null or undefined`, input);
        throw new TypeError(errorMessage);
    }
}
