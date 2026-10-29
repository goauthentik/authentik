import { BookmarkChangeEvent } from "./bookmarkChangeEvent";
import { type Bookmark, readState, writeState } from "./bookmarkState";

import { type AdminInterface } from "#admin/ak-interface-admin";

import { match } from "ts-pattern";

import { ContextProvider, createContext } from "@lit/context";
import { ReactiveController } from "lit";

export { type Bookmark };

export const BookmarkContext = createContext<Bookmark[] | null>(
    Symbol("authentik-bookmark-context"),
);

export class BookmarkController implements ReactiveController {
    protected provider: ContextProvider<typeof BookmarkContext>;

    #abortController: AbortController | null = null;

    constructor(protected host: AdminInterface) {
        this.provider = new ContextProvider(host, {
            context: BookmarkContext,
            initialValue: null,
        });

        host.addController(this);
    }

    public get bookmarks(): Bookmark[] {
        return this.provider.value ? [...this.provider.value] : [];
    }

    protected bookmarkChangeRequest = (event: BookmarkChangeEvent) => {
        const { add, path, label } = event;

        // prettier-ignore
        const newValueCollection = match(add)
            .with(true, () => ([...(this.provider.value ?? []), { path, label }]))
            .with(false, () => (this.provider.value ?? []).filter((bookmark) => bookmark.path !== path))
            .exhaustive();

        const seen = new Set<string>();

        const newValue = newValueCollection.reduce(
            (values: Bookmark[], value: Bookmark): Bookmark[] => {
                if (seen.has(value.path)) {
                    return values;
                }

                seen.add(value.path);

                return [...values, value];
            },
            [],
        );

        writeState(newValue);
        this.provider.value = newValue;
        this.host.requestUpdate();
    };

    hostConnected() {
        this.#abortController?.abort();
        const { signal } = (this.#abortController = new AbortController());

        window.addEventListener(BookmarkChangeEvent.eventName, this.bookmarkChangeRequest, {
            signal,
        });

        this.provider.value = readState();
    }

    hostDisconnected() {
        this.#abortController?.abort();
        this.#abortController = null;
    }
}
