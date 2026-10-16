/**
 * @file The search modal. A native `<dialog>` opened with `showModal()` supplies the focus trap,
 *   the inert background, the backdrop, the close on Escape and the return of focus to the
 *   opener. The query field is an `<input type="search">` with the ARIA combobox role. DOM focus
 *   stays on the input, and `aria-activedescendant` identifies the selected hit. The component
 *   owns no data access: `search` is passed in. Recent queries are a per-reader convenience in
 *   `localStorage`; the modal renders the same without them.
 */

import { hitHref, type SearchHit, type SearchResponse } from "#search/common.mjs";

import React, {
    type KeyboardEvent,
    type MouseEvent,
    type ReactNode,
    useEffect,
    useId,
    useMemo,
    useRef,
    useState,
} from "react";

export interface SearchModalProps {
    open: boolean;
    /**
     * The label of the site being served. A hit on another site is grouped under that site's
     * name.
     */
    site: string;
    onClose: () => void;
    /**
     * Called with the hit's link on Enter or on an unmodified click. Absent, the link navigates
     * as an ordinary anchor.
     */
    onNavigate?: (href: string) => void;
    /**
     * Runs the query.
     *
     * The function must keep a stable identity across renders (for example through
     * `useCallback`), because a new identity refires the request for the current query.
     */
    search: (query: string, signal: AbortSignal) => Promise<SearchResponse>;
    /**
     * The `localStorage` key under which recent queries are kept. Absent, recent queries are
     * not kept.
     */
    recentKey?: string;
}

type Status =
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "results"; response: SearchResponse }
    | { kind: "failed" };

const DEBOUNCE_MS = 150;

/**
 * How long a request runs before the live region announces that the index is loading.
 */
const LOADING_ANNOUNCE_MS = 300;
const MAX_QUERY_LENGTH = 200;
const DEFAULT_CATEGORY = "Documentation";
const RECENT_LIMIT = 5;

function useDebouncedValue<T>(value: T, delayMs: number): T {
    const [debounced, setDebounced] = useState(value);

    useEffect(() => {
        const id = setTimeout(() => setDebounced(value), delayMs);

        return () => clearTimeout(id);
    }, [value, delayMs]);

    return debounced;
}

function statusText(status: Status): string {
    if (status.kind === "failed") return "Search is unavailable. Try again in a moment.";

    if (status.kind === "loading") return "Loading the search index…";

    if (status.kind === "idle") return "";

    const { response } = status;

    if (!response.hits.length) return `No results for “${response.query}”.`;

    return response.hits.length === 1 ? "1 result." : `${response.hits.length} results.`;
}

/**
 * The ranges of `text` that match a query token, case-insensitively, for emphasis in a title.
 */
function tokenRanges(text: string, query: string): [number, number][] {
    const lower = text.toLowerCase();
    const ranges: [number, number][] = [];

    for (const token of new Set(
        query
            .toLowerCase()
            .split(/\s+/)
            .filter((part) => part.length >= 2),
    )) {
        for (
            let index = lower.indexOf(token);
            index >= 0;
            index = lower.indexOf(token, index + token.length)
        ) {
            ranges.push([index, index + token.length]);
        }
    }

    return ranges.toSorted((a, b) => a[0] - b[0]);
}

function emphasized(text: string, ranges: readonly [number, number][]): ReactNode[] {
    const parts: ReactNode[] = [];
    let cursor = 0;

    for (const [start, end] of ranges) {
        if (start < cursor) continue;

        parts.push(text.slice(cursor, start), <mark key={start}>{text.slice(start, end)}</mark>);
        cursor = end;
    }

    parts.push(text.slice(cursor));

    return parts;
}

/**
 * The deepest heading of a hit is its title. The headings between the category and it are its
 * path.
 */
function headings(hit: SearchHit): { title: string; path: string[] } {
    const named = hit.hierarchy.slice(1).filter((entry): entry is string => entry !== null);
    const title = named.at(-1) ?? hit.url;

    return { title, path: named.slice(0, -1) };
}

function readRecent(key: string | undefined): string[] {
    if (!key) return [];

    try {
        const raw = globalThis.localStorage.getItem(key);
        const stored: unknown = raw === null ? [] : JSON.parse(raw);

        return Array.isArray(stored)
            ? (stored as unknown[]).filter((entry): entry is string => typeof entry === "string")
            : [];
    } catch {
        return [];
    }
}

function writeRecent(key: string | undefined, entries: readonly string[]): void {
    if (!key) return;

    try {
        globalThis.localStorage.setItem(key, JSON.stringify(entries));
    } catch {
        // Storage can be absent or blocked. The modal works without it.
    }
}

const SearchIcon = () => (
    <svg className="ak-search__icon" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
        <circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" strokeWidth="2" />
        <path
            d="M13 13l4.5 4.5"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
        />
    </svg>
);

const Spinner = () => (
    <svg
        className="ak-search__icon ak-search__icon--spinning"
        viewBox="0 0 20 20"
        aria-hidden="true"
        focusable="false"
    >
        <circle
            cx="10"
            cy="10"
            r="7"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeDasharray="22 22"
            strokeLinecap="round"
        />
    </svg>
);

export function SearchModal({
    open,
    site,
    onClose,
    onNavigate,
    search,
    recentKey,
}: SearchModalProps) {
    const dialogRef = useRef<HTMLDialogElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    const baseID = useId();
    const listboxID = `${baseID}-listbox`;
    const [query, setQuery] = useState("");
    const [settled, setSettled] = useState<Status>({ kind: "idle" });
    const [selected, setSelected] = useState(0);
    const [loading, setLoading] = useState(false);
    const [recent, setRecent] = useState<string[]>([]);
    const trimmed = query.trim().slice(0, MAX_QUERY_LENGTH);
    const debounced = useDebouncedValue(trimmed, DEBOUNCE_MS);

    useEffect(() => {
        const dialog = dialogRef.current;

        if (!dialog) return;

        if (open && !dialog.open) {
            dialog.showModal();
            inputRef.current?.focus();
            setRecent(readRecent(recentKey));
        } else if (!open && dialog.open) {
            dialog.close();
        }
    }, [open, recentKey]);

    useEffect(() => {
        if (debounced === "") return;

        // The abort of the earlier request keeps a late response from replacing newer results.
        const controller = new AbortController();
        const loadingTimer = setTimeout(() => setLoading(true), LOADING_ANNOUNCE_MS);

        search(debounced, controller.signal).then(
            (response) => {
                if (controller.signal.aborted) return;

                clearTimeout(loadingTimer);
                setLoading(false);
                setSettled({ kind: "results", response });
                setSelected(0);
            },
            () => {
                if (controller.signal.aborted) return;

                clearTimeout(loadingTimer);
                setLoading(false);
                setSettled({ kind: "failed" });
            },
        );

        return () => {
            clearTimeout(loadingTimer);
            setLoading(false);
            controller.abort();
        };
    }, [debounced, search]);

    // An empty query shows no results, whatever the last settled response was.
    const status: Status = debounced === "" ? { kind: "idle" } : settled;
    const response = status.kind === "results" ? status.response : undefined;
    // The announcement reports a slow request while the last results stay on screen.
    const announced: Status = loading && debounced !== "" ? { kind: "loading" } : status;

    const groups = useMemo(() => {
        const hits = response?.hits ?? [];
        const byGroup = new Map<string, SearchHit[]>();

        for (const hit of hits) {
            const category = hit.hierarchy[0] ?? DEFAULT_CATEGORY;
            const group = hit.site === site ? category : `${hit.site} › ${category}`;

            byGroup.set(group, [...(byGroup.get(group) ?? []), hit]);
        }

        // Options are numbered in display order so the arrow keys follow what the reader sees.
        let order = 0;

        return [...byGroup].map(([group, entries]) => ({
            group,
            entries: entries.map((hit) => ({ hit, order: order++ })),
        }));
    }, [response, site]);

    const ordered = groups.flatMap((group) => group.entries);
    const optionID = (order: number) => `${baseID}-option-${order}`;
    const emphasis = response?.corrected ?? debounced;

    function remember(text: string) {
        const entries = [text, ...recent.filter((entry) => entry !== text)].slice(0, RECENT_LIMIT);

        setRecent(entries);
        writeRecent(recentKey, entries);
    }

    function forget(text: string) {
        const entries = recent.filter((entry) => entry !== text);

        setRecent(entries);
        writeRecent(recentKey, entries);
    }

    function go(hit: SearchHit) {
        const href = hitHref(hit);

        if (trimmed !== "") {
            remember(trimmed);
        }

        onClose();

        if (onNavigate) {
            onNavigate(href);
        } else {
            globalThis.location.assign(href);
        }
    }

    function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
        // A key that commits or edits an IME composition is not a command.
        if (event.nativeEvent.isComposing) return;

        // A search input clears itself on Escape before the dialog sees the key; the reader
        // expects the modal to close.
        if (event.key === "Escape") {
            event.preventDefault();
            dialogRef.current?.close();
            return;
        }

        if (!ordered.length) return;

        const last = ordered.length - 1;
        let next: number | undefined;

        switch (event.key) {
            case "ArrowDown":
                next = selected === last ? 0 : selected + 1;
                break;
            case "ArrowUp":
                next = selected === 0 ? last : selected - 1;
                break;
            case "Home":
                next = 0;
                break;
            case "End":
                next = last;
                break;
            default:
                break;
        }

        if (next !== undefined) {
            event.preventDefault();
            setSelected(next);
            document.getElementById(optionID(next))?.scrollIntoView({ block: "nearest" });
        } else if (event.key === "Enter") {
            event.preventDefault();

            // The hits on screen answer an earlier query until the debounce settles.
            if (trimmed !== debounced) return;

            const entry = ordered[selected];

            if (entry) {
                go(entry.hit);
            }
        }
    }

    function onDialogClick(event: MouseEvent<HTMLDialogElement>) {
        // A click whose target is the dialog element itself landed on the backdrop.
        if (event.target === event.currentTarget) {
            event.currentTarget.close();
        }
    }

    function onLinkClick(event: MouseEvent<HTMLAnchorElement>, hit: SearchHit) {
        if (
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey ||
            event.button !== 0
        ) {
            return;
        }

        event.preventDefault();
        go(hit);
    }

    const showRecent = trimmed === "" && recent.length > 0;
    const noResults = response !== undefined && response.hits.length === 0;

    return (
        <dialog
            ref={dialogRef}
            className="ak-search"
            aria-label="Search the documentation"
            onClose={onClose}
            onClick={onDialogClick}
        >
            <form
                role="search"
                className="ak-search__form"
                onSubmit={(event) => event.preventDefault()}
            >
                <label className="ak-search__field">
                    {loading ? <Spinner /> : <SearchIcon />}
                    <input
                        ref={inputRef}
                        type="search"
                        className="ak-search__input"
                        role="combobox"
                        aria-label="Search the documentation"
                        aria-autocomplete="list"
                        aria-expanded={ordered.length > 0}
                        aria-controls={listboxID}
                        aria-activedescendant={ordered.length ? optionID(selected) : undefined}
                        autoComplete="off"
                        spellCheck={false}
                        maxLength={MAX_QUERY_LENGTH}
                        placeholder="Search the documentation"
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        onKeyDown={onKeyDown}
                    />
                </label>
                <button
                    type="button"
                    className="ak-search__cancel"
                    onClick={() => dialogRef.current?.close()}
                >
                    Cancel
                </button>
            </form>

            {response?.corrected != null && (
                <p className="ak-search__corrected">Showing results for “{response.corrected}”</p>
            )}

            <div className="ak-search__body">
                {showRecent && (
                    <section className="ak-search__recent" aria-label="Recent searches">
                        <div className="ak-search__category">Recent</div>
                        <ul className="ak-search__recent-list">
                            {recent.map((entry) => (
                                <li key={entry} className="ak-search__recent-item">
                                    <button
                                        type="button"
                                        className="ak-search__recent-query"
                                        onClick={() => setQuery(entry)}
                                    >
                                        {entry}
                                    </button>
                                    <button
                                        type="button"
                                        className="ak-search__recent-remove"
                                        aria-label={`Remove “${entry}” from recent searches`}
                                        onClick={() => forget(entry)}
                                    >
                                        ×
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </section>
                )}

                {noResults && (
                    <p className="ak-search__empty">
                        No results for “{response.query}”. Try a different spelling or a shorter
                        query.
                    </p>
                )}

                <div
                    id={listboxID}
                    role="listbox"
                    aria-label="Search results"
                    className="ak-search__results"
                >
                    {groups.map((group, groupIndex) => (
                        <div
                            key={group.group}
                            role="group"
                            aria-labelledby={`${baseID}-group-${groupIndex}`}
                            className="ak-search__group"
                        >
                            <div
                                id={`${baseID}-group-${groupIndex}`}
                                className="ak-search__category"
                            >
                                {group.group}
                            </div>
                            {group.entries.map(({ hit, order }) => {
                                const { title, path } = headings(hit);

                                return (
                                    // The option is the link itself: an option may not contain an
                                    // interactive element, and `option` is an allowed role on
                                    // `a[href]`, which keeps the URL for open-in-new-tab.
                                    <a
                                        key={order}
                                        id={optionID(order)}
                                        role="option"
                                        aria-selected={order === selected}
                                        href={hitHref(hit)}
                                        tabIndex={-1}
                                        className={`ak-search__option ${hit.anchor === "" ? "ak-search__option--page" : "ak-search__option--section"}`}
                                        onPointerMove={() => setSelected(order)}
                                        onClick={(event) => onLinkClick(event, hit)}
                                    >
                                        {path.length > 0 && (
                                            <span className="ak-search__path">
                                                {path.join(" › ")}
                                            </span>
                                        )}
                                        <span className="ak-search__title">
                                            {emphasized(title, tokenRanges(title, emphasis))}
                                        </span>
                                        {hit.snippet !== "" && (
                                            <span className="ak-search__snippet">
                                                {emphasized(hit.snippet, hit.highlights)}
                                            </span>
                                        )}
                                    </a>
                                );
                            })}
                        </div>
                    ))}
                </div>
            </div>

            <footer className="ak-search__footer">
                <p aria-live="polite" className="ak-search__status">
                    {statusText(announced)}
                </p>
                <ul className="ak-search__hints" aria-label="Keyboard shortcuts">
                    <li>
                        <kbd>↵</kbd> open
                    </li>
                    <li>
                        <kbd>↑</kbd>
                        <kbd>↓</kbd> move
                    </li>
                    <li>
                        <kbd>esc</kbd> close
                    </li>
                </ul>
            </footer>
        </dialog>
    );
}
