/**
 * @file The search modal, rendered with DocSearch's markup inside a native `<dialog>`. The dialog,
 *   opened with `showModal()`, supplies the focus trap, the inert background, the close on Escape
 *   and the return of focus to the opener. The query field is an `<input type="search">` with the
 *   ARIA combobox role; DOM focus stays on it and `aria-activedescendant` identifies the selected
 *   hit. The component owns no data access: `search` is passed in. Recently opened hits are a
 *   per-reader convenience in `localStorage`; the modal renders the same without them.
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
     * The `localStorage` key under which recently opened hits are kept. Absent, they are not
     * kept.
     */
    recentKey?: string;
}

/**
 * A hit the reader opened earlier, kept without its snippet.
 */
type RecentHit = Pick<SearchHit, "site" | "url" | "anchor" | "hierarchy">;

type Status =
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "results"; response: SearchResponse }
    | { kind: "failed" };

const DEBOUNCE_MS = 150;

/**
 * How long a request runs before the spinner replaces the magnifier.
 */
const LOADING_ANNOUNCE_MS = 300;
const MAX_QUERY_LENGTH = 200;
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
 * The named headings of a hit below the category: the page title, then its section path.
 */
function headings(hit: Pick<SearchHit, "hierarchy" | "url">): string[] {
    const named = hit.hierarchy.slice(1).filter((entry): entry is string => entry !== null);

    return named.length ? named : [hit.url];
}

function isRecentHit(value: unknown): value is RecentHit {
    if (typeof value !== "object" || value === null) return false;

    const entry = value as Record<string, unknown>;

    return (
        typeof entry.site === "string" &&
        typeof entry.url === "string" &&
        typeof entry.anchor === "string" &&
        Array.isArray(entry.hierarchy)
    );
}

function readRecent(key: string | undefined): RecentHit[] {
    if (!key) return [];

    try {
        const raw = globalThis.localStorage.getItem(key);
        const stored: unknown = raw === null ? [] : JSON.parse(raw);

        return Array.isArray(stored) ? (stored as unknown[]).filter(isRecentHit) : [];
    } catch {
        return [];
    }
}

function writeRecent(key: string | undefined, entries: readonly RecentHit[]): void {
    if (!key) return;

    try {
        globalThis.localStorage.setItem(key, JSON.stringify(entries));
    } catch {
        // Storage can be absent or blocked. The modal works without it.
    }
}

function sameHit(a: RecentHit, b: RecentHit): boolean {
    return a.site === b.site && a.url === b.url && a.anchor === b.anchor;
}

//#region Icons

/**
 * The icons DocSearch draws, so the hits read as they did.
 */

export function SearchIcon({ className }: { className?: string }) {
    return (
        <svg width="20" height="20" className={className} viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="11" cy="11" r="8" stroke="currentColor" fill="none" strokeWidth="1.4" />
            <path
                d="m21 21-4.3-4.3"
                stroke="currentColor"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
}

const LoadingIcon = () => (
    <svg viewBox="0 0 38 38" stroke="currentColor" strokeOpacity=".5" aria-hidden="true">
        <g fill="none" fillRule="evenodd">
            <g transform="translate(1 1)" strokeWidth="2">
                <circle strokeOpacity=".3" cx="18" cy="18" r="18" />
                <path d="M36 18c0-9.94-8.06-18-18-18">
                    <animateTransform
                        attributeName="transform"
                        type="rotate"
                        from="0 18 18"
                        to="360 18 18"
                        dur="1s"
                        repeatCount="indefinite"
                    />
                </path>
            </g>
        </g>
    </svg>
);

const CloseIcon = () => (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
        <path
            d="M10 10l5.09-5.09L10 10l5.09 5.09L10 10zm0 0L4.91 4.91 10 10l-5.09 5.09L10 10z"
            stroke="currentColor"
            fill="none"
            fillRule="evenodd"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
    </svg>
);

const PageIcon = () => (
    <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
    >
        <path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" />
        <path d="M14 2v4a2 2 0 0 0 2 2h4" />
        <path d="M10 9H8" />
        <path d="M16 13H8" />
        <path d="M16 17H8" />
    </svg>
);

const AnchorIcon = () => (
    <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
    >
        <line x1="4" x2="20" y1="9" y2="9" />
        <line x1="4" x2="20" y1="15" y2="15" />
        <line x1="10" x2="8" y1="3" y2="21" />
        <line x1="16" x2="14" y1="3" y2="21" />
    </svg>
);

const ContentIcon = () => (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
        <path
            d="M17 5H3h14zm0 5H3h14zm0 5H3h14z"
            stroke="currentColor"
            fill="none"
            fillRule="evenodd"
            strokeLinejoin="round"
        />
    </svg>
);

const RecentIcon = () => (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
        <g
            stroke="currentColor"
            fill="none"
            fillRule="evenodd"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M3.18 6.6a8.23 8.23 0 1112.93 9.94h0a8.23 8.23 0 01-11.63 0" />
            <path d="M6.44 7.25H2.55V3.36M10.45 6v5.6M10.45 11.6L13 13" />
        </g>
    </svg>
);

const SelectIcon = () => (
    <svg
        className="DocSearch-Hit-Select-Icon"
        width="20"
        height="20"
        viewBox="0 0 20 20"
        aria-hidden="true"
    >
        <g
            stroke="currentColor"
            fill="none"
            fillRule="evenodd"
            strokeLinecap="round"
            strokeLinejoin="round"
        >
            <path d="M18 3v4c0 2-2 4-4 4H2" />
            <path d="M8 17l-6-6 6-6" />
        </g>
    </svg>
);

const NoResultsIcon = () => (
    <svg
        width="64"
        height="64"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
    >
        <path d="m13.5 8.5-5 5" />
        <path d="m8.5 8.5 5 5" />
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
    </svg>
);

const ErrorIcon = () => (
    <svg
        width="64"
        height="64"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
    >
        <circle cx="12" cy="12" r="10" />
        <line x1="12" x2="12" y1="8" y2="12" />
        <line x1="12" x2="12.01" y1="16" y2="16" />
    </svg>
);

const ArrowDownIcon = () => (
    <svg width="20" height="20" aria-label="Arrow down" viewBox="0 0 24 24" role="img">
        <g
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.4"
        >
            <path d="M12 5v14" />
            <path d="m19 12-7 7-7-7" />
        </g>
    </svg>
);

const ArrowUpIcon = () => (
    <svg width="20" height="20" aria-label="Arrow up" viewBox="0 0 24 24" role="img">
        <g
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.4"
        >
            <path d="m5 12 7-7 7 7" />
            <path d="M12 19V5" />
        </g>
    </svg>
);

const EnterIcon = () => (
    <svg width="20" height="20" aria-label="Enter key" viewBox="0 0 24 24" role="img">
        <g
            fill="none"
            stroke="currentColor"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="1.4"
        >
            <polyline points="9 10 4 15 9 20" />
            <path d="M20 4v7a4 4 0 0 1-4 4H4" />
        </g>
    </svg>
);

//#endregion

/**
 * How a hit is drawn: a page by its title, a section by its heading, and a section whose match
 * sits in its body by the matching excerpt, as DocSearch draws an anchor and a content hit.
 */
type HitKind = "page" | "anchor" | "content";

function hitKind(hit: SearchHit, query: string, title: string): HitKind {
    if (hit.anchor === "") return "page";

    if (tokenRanges(title, query).length > 0 || hit.highlights.length === 0) return "anchor";

    return "content";
}

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
    const labelID = `${baseID}-label`;
    const [query, setQuery] = useState("");
    const [settled, setSettled] = useState<Status>({ kind: "idle" });
    const [selected, setSelected] = useState(0);
    const [loading, setLoading] = useState(false);
    const [recent, setRecent] = useState<RecentHit[]>([]);
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

    // An empty query shows the recent hits, whatever the last settled response was.
    const status: Status = debounced === "" ? { kind: "idle" } : settled;
    const response = status.kind === "results" ? status.response : undefined;
    // The announcement reports a slow request while the last results stay on screen.
    const announced: Status = loading && debounced !== "" ? { kind: "loading" } : status;
    const emphasis = response?.corrected ?? debounced;

    const groups = useMemo(() => {
        const hits = response?.hits ?? [];
        const byGroup = new Map<string, SearchHit[]>();

        for (const hit of hits) {
            const category = hit.hierarchy[0] ?? site;
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

    const showRecent = status.kind === "idle";
    const ordered: { hit: RecentHit; order: number }[] = showRecent
        ? recent.map((hit, order) => ({ hit, order }))
        : groups.flatMap((group) => group.entries);
    const optionID = (order: number) => `${baseID}-option-${order}`;
    const listboxIDs = showRecent
        ? [`${baseID}-recent`]
        : groups.map((_group, index) => `${baseID}-list-${index}`);

    function remember(hit: RecentHit) {
        const entry: RecentHit = {
            site: hit.site,
            url: hit.url,
            anchor: hit.anchor,
            hierarchy: hit.hierarchy,
        };
        const entries = [entry, ...recent.filter((other) => !sameHit(other, entry))].slice(
            0,
            RECENT_LIMIT,
        );

        setRecent(entries);
        writeRecent(recentKey, entries);
    }

    function forget(hit: RecentHit) {
        const entries = recent.filter((other) => !sameHit(other, hit));

        setRecent(entries);
        writeRecent(recentKey, entries);
        setSelected(0);
    }

    function go(hit: RecentHit) {
        const href = hitHref(hit);

        remember(hit);
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
        // The dialog is the full-viewport overlay, so a click whose target is the dialog element
        // itself landed outside the modal.
        if (event.target === event.currentTarget) {
            event.currentTarget.close();
        }
    }

    function onLinkClick(event: MouseEvent<HTMLAnchorElement>, hit: RecentHit) {
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

    function clear() {
        setQuery("");
        inputRef.current?.focus();
    }

    function renderHit(hit: SearchHit, order: number) {
        const path = headings(hit);
        const title = path.at(-1) ?? hit.url;
        const kind = hitKind(hit, emphasis, title);
        const parent = path.at(-2);

        return (
            <li
                key={order}
                className="DocSearch-Hit"
                id={optionID(order)}
                role="option"
                aria-selected={order === selected}
            >
                <a
                    href={hitHref(hit)}
                    tabIndex={-1}
                    onPointerMove={() => setSelected(order)}
                    onClick={(event) => onLinkClick(event, hit)}
                >
                    <div className="DocSearch-Hit-Container">
                        <div className="DocSearch-Hit-icon">
                            {kind === "page" ? (
                                <PageIcon />
                            ) : kind === "anchor" ? (
                                <AnchorIcon />
                            ) : (
                                <ContentIcon />
                            )}
                        </div>
                        <div className="DocSearch-Hit-content-wrapper">
                            {kind === "content" ? (
                                <>
                                    <span className="DocSearch-Hit-title">
                                        {emphasized(hit.snippet, hit.highlights)}
                                    </span>
                                    <span className="DocSearch-Hit-path">
                                        {emphasized(title, tokenRanges(title, emphasis))}
                                    </span>
                                </>
                            ) : (
                                <>
                                    <span className="DocSearch-Hit-title">
                                        {emphasized(title, tokenRanges(title, emphasis))}
                                    </span>
                                    {parent !== undefined && (
                                        <span className="DocSearch-Hit-path">
                                            {emphasized(parent, tokenRanges(parent, emphasis))}
                                        </span>
                                    )}
                                </>
                            )}
                        </div>
                        <div className="DocSearch-Hit-action">
                            <SelectIcon />
                        </div>
                    </div>
                </a>
            </li>
        );
    }

    function renderRecent(hit: RecentHit, order: number) {
        const path = headings(hit);
        const title = path.at(-1) ?? hit.url;
        const parent = path.at(-2);

        return (
            <li
                key={order}
                className="DocSearch-Hit"
                id={optionID(order)}
                role="option"
                aria-selected={order === selected}
            >
                <a
                    href={hitHref(hit)}
                    tabIndex={-1}
                    onPointerMove={() => setSelected(order)}
                    onClick={(event) => onLinkClick(event, hit)}
                >
                    <div className="DocSearch-Hit-Container">
                        <div className="DocSearch-Hit-icon">
                            <RecentIcon />
                        </div>
                        <div className="DocSearch-Hit-content-wrapper">
                            <span className="DocSearch-Hit-title">{title}</span>
                            {parent !== undefined && (
                                <span className="DocSearch-Hit-path">{parent}</span>
                            )}
                        </div>
                        <div className="DocSearch-Hit-action">
                            <button
                                type="button"
                                className="DocSearch-Hit-action-button"
                                title="Remove this search from history"
                                aria-label={`Remove “${title}” from recent searches`}
                                onClick={(event) => {
                                    event.preventDefault();
                                    event.stopPropagation();
                                    forget(hit);
                                }}
                            >
                                <CloseIcon />
                            </button>
                        </div>
                    </div>
                </a>
            </li>
        );
    }

    function renderScreen(): ReactNode {
        if (status.kind === "failed") {
            return (
                <div className="DocSearch-ErrorScreen">
                    <div className="DocSearch-Screen-Icon">
                        <ErrorIcon />
                    </div>
                    <p className="DocSearch-Title">Unable to load the search index</p>
                    <p className="DocSearch-Help">Try again in a moment.</p>
                </div>
            );
        }

        if (showRecent) {
            if (!recent.length) {
                return (
                    <div className="DocSearch-StartScreen">
                        <p className="DocSearch-Help">No recent searches</p>
                    </div>
                );
            }

            return (
                <section className="DocSearch-Hits">
                    <div className="DocSearch-Hit-source">Recent</div>
                    <ul role="listbox" aria-labelledby={labelID} id={`${baseID}-recent`}>
                        {recent.map((hit, order) => renderRecent(hit, order))}
                    </ul>
                </section>
            );
        }

        if (response !== undefined && response.hits.length === 0) {
            return (
                <div className="DocSearch-NoResults">
                    <div className="DocSearch-Screen-Icon">
                        <NoResultsIcon />
                    </div>
                    <p className="DocSearch-Title">
                        No results found for &quot;<strong>{response.query}</strong>&quot;
                    </p>
                </div>
            );
        }

        return (
            <>
                {response?.corrected != null && (
                    <p className="DocSearch-Help DocSearch-Corrected">
                        Showing results for &quot;<strong>{response.corrected}</strong>&quot;
                    </p>
                )}
                {groups.map((group, index) => (
                    <section key={group.group} className="DocSearch-Hits">
                        <div className="DocSearch-Hit-source">{group.group}</div>
                        <ul role="listbox" aria-labelledby={labelID} id={`${baseID}-list-${index}`}>
                            {group.entries.map(({ hit, order }) => renderHit(hit, order))}
                        </ul>
                    </section>
                ))}
            </>
        );
    }

    return (
        <dialog
            ref={dialogRef}
            className="DocSearch DocSearch-Container"
            aria-label="Search the documentation"
            onClose={onClose}
            onClick={onDialogClick}
        >
            <div className="DocSearch-Modal">
                <header className="DocSearch-SearchBar">
                    <form
                        className="DocSearch-Form"
                        role="search"
                        onSubmit={(event) => event.preventDefault()}
                        onReset={(event) => {
                            event.preventDefault();
                            clear();
                        }}
                    >
                        {loading ? (
                            <div className="DocSearch-LoadingIndicator">
                                <LoadingIcon />
                            </div>
                        ) : (
                            <label
                                className="DocSearch-MagnifierLabel"
                                htmlFor={`${baseID}-input`}
                                id={labelID}
                            >
                                <SearchIcon className="DocSearch-Search-Icon" />
                                <span className="DocSearch-VisuallyHiddenForAccessibility">
                                    Search
                                </span>
                            </label>
                        )}
                        <input
                            ref={inputRef}
                            id={`${baseID}-input`}
                            type="search"
                            className="DocSearch-Input"
                            role="combobox"
                            aria-labelledby={labelID}
                            aria-autocomplete="list"
                            aria-expanded={ordered.length > 0}
                            aria-controls={listboxIDs.join(" ")}
                            aria-activedescendant={ordered.length ? optionID(selected) : undefined}
                            autoComplete="off"
                            autoCorrect="off"
                            autoCapitalize="off"
                            enterKeyHint="search"
                            spellCheck={false}
                            maxLength={MAX_QUERY_LENGTH}
                            placeholder="Search docs"
                            value={query}
                            onChange={(event) => setQuery(event.target.value)}
                            onKeyDown={onKeyDown}
                        />
                        <div className="DocSearch-Actions">
                            {query !== "" && (
                                <>
                                    <button
                                        type="reset"
                                        className="DocSearch-Clear"
                                        aria-label="Clear the query"
                                    >
                                        Clear the query
                                    </button>
                                    <div className="DocSearch-Divider" />
                                </>
                            )}
                            <button
                                type="button"
                                title="Cancel"
                                className="DocSearch-Action DocSearch-Close"
                                aria-label="Cancel"
                                onClick={() => dialogRef.current?.close()}
                            >
                                <CloseIcon />
                            </button>
                        </div>
                    </form>
                    <button
                        type="button"
                        className="DocSearch-Cancel"
                        onClick={() => dialogRef.current?.close()}
                    >
                        Cancel
                    </button>
                </header>

                <div className="DocSearch-Dropdown">
                    <div className="DocSearch-Dropdown-Container">{renderScreen()}</div>
                </div>

                <footer className="DocSearch-Footer">
                    <p aria-live="polite" className="DocSearch-Status">
                        {statusText(announced)}
                    </p>
                    <ul className="DocSearch-Commands">
                        <li>
                            <kbd className="DocSearch-Commands-Key">
                                <ArrowDownIcon />
                            </kbd>
                            <kbd className="DocSearch-Commands-Key">
                                <ArrowUpIcon />
                            </kbd>
                            <span className="DocSearch-Label">Navigate</span>
                        </li>
                        <li>
                            <kbd className="DocSearch-Commands-Key">
                                <EnterIcon />
                            </kbd>
                            <span className="DocSearch-Label">Select</span>
                        </li>
                        <li>
                            <kbd className="DocSearch-Commands-Key">
                                <span className="DocSearch-Escape-Key">ESC</span>
                            </kbd>
                            <span className="DocSearch-Label" aria-label="Escape key">
                                Close
                            </span>
                        </li>
                    </ul>
                </footer>
            </div>
        </dialog>
    );
}
