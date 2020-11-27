import { NotFoundError, RequestError } from "./errors";

export const VERSION = "v2beta";

export class Client {
    makeUrl(...url: string[]): string {
        return `/api/${VERSION}/${url.join("/")}/`;
    }

    fetch<T>(...url: string[]): Promise<T> {
        return fetch(this.makeUrl(...url))
            .then((r) => {
                if (r.status > 300) {
                    switch (r.status) {
                        case 404:
                            throw new NotFoundError(`URL ${this.makeUrl(...url)} not found`);
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
