import { NotFoundError, RequestError } from "./errors";

export const VERSION = "v2beta";

export class Client {
    makeUrl(url: string[], query?: { [key: string]: string }): string {
        let builtUrl = `/api/${VERSION}/${url.join("/")}/`;
        if (query) {
            let queryString = Object.keys(query)
                .map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(query[k]))
                .join("&");
            builtUrl += `?${queryString}`;
        }
        return builtUrl;
    }

    fetch<T>(url: string[], query?: { [key: string]: string }): Promise<T> {
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
}

export const DefaultClient = new Client();

export interface PBResponse {
    count: number;
    next: string;
    previous: string;
    results: Array<any>;
}
