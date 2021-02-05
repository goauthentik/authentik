import { getCookie } from "../utils";
import { NotFoundError, RequestError } from "./Error";

export const VERSION = "v2beta";

export interface QueryArguments {
    [key: string]: number | string | boolean | null;
}

export class Client {
    makeUrl(url: string[], query?: QueryArguments): string {
        let builtUrl = `/api/${VERSION}/${url.join("/")}/`;
        if (query) {
            const queryString = Object.keys(query)
                .filter((k) => query[k] !== null)
                // we default to a string in query[k] as we've filtered out the null above
                // this is just for type-hinting
                .map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(query[k] || ""))
                .join("&");
            builtUrl += `?${queryString}`;
        }
        return builtUrl;
    }

    fetch<T>(url: string[], query?: QueryArguments): Promise<T> {
        const finalUrl = this.makeUrl(url, query);
        return fetch(finalUrl)
            .then((r) => {
                if (r.status > 300) {
                    switch (r.status) {
                    case 404:
                        throw new NotFoundError(`URL ${finalUrl} not found`);
                    default:
                        throw new RequestError(r.statusText);
                    }
                }
                return r;
            })
            .then((r) => r.json())
            .then((r) => <T>r);
    }

    update<T>(url: string[], body: T, query?: QueryArguments): Promise<T> {
        const finalUrl = this.makeUrl(url, query);
        const csrftoken = getCookie("authentik_csrf");
        const request = new Request(finalUrl, {
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken,
                },
        });
        return fetch(request, {
            method: "PATCH",
            mode: "same-origin",
            body: JSON.stringify(body),
        })
            .then((r) => {
                if (r.status > 300) {
                    switch (r.status) {
                    case 404:
                        throw new NotFoundError(`URL ${finalUrl} not found`);
                    default:
                        throw new RequestError(r.statusText);
                    }
                }
                return r;
            })
            .then((r) => r.json())
            .then((r) => <T>r);
    }
}

export const DefaultClient = new Client();

export interface PBPagination {
    next?: number;
    previous?: number;

    count: number;
    current: number;
    total_pages: number;

    start_index: number;
    end_index: number;
}

export interface PBResponse<T> {
    pagination: PBPagination;

    results: Array<T>;
}
