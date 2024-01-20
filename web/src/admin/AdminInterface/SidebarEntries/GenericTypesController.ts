import { ReactiveControllerHost } from "lit";

import { TypeCreate } from "@goauthentik/api";

import { LocalSidebarEntry } from "../AdminSidebar";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Fetcher = () => Promise<TypeCreate[]>;

const typeCreateToSidebar = (baseUrl: string, tcreate: TypeCreate[]): LocalSidebarEntry[] =>
    tcreate.map((t) => [
        `${baseUrl};${encodeURIComponent(JSON.stringify({ search: t.name }))}`,
        t.name,
    ]);

/**
 * createTypesController
 *
 * The Sidebar accesses a number objects of `TypeCreate`, which all have the exact same type, just
 * different accessors for generating the lists and different paths to which they respond. This
 * function is a template for a (simple) reactive controller that fetches the data for that type on
 * construction, then informs the host that the data is available.
 */

/**
 * TODO (2023-11-17): This function is unlikely to survive in this form. It would be nice if it were more
 * generic, able to take a converter that can handle more that TypeCreate[] as its inbound argument,
 * since we need to refine what's displayed and on what the search is conducted.
 *
 */

export function createTypesController(
    fetch: Fetcher,
    path: string,
    converter = typeCreateToSidebar,
) {
    return class GenericTypesController {
        createTypes: TypeCreate[] = [];
        host: ReactiveControllerHost;

        constructor(host: ReactiveControllerHost) {
            this.host = host;
            fetch().then((types) => {
                this.createTypes = types;
                host.requestUpdate();
            });
        }

        entries(): LocalSidebarEntry[] {
            return converter(path, this.createTypes);
        }
    };
}

export default createTypesController;
