/**
 * @file The navbar search control. It replaces the theme's empty `SearchBar` slot with DocSearch's
 *   button markup, opens the search modal on a click, on Ctrl+K or Cmd+K, and on `/` pressed
 *   outside a text field. The index is opened in a worker when the modal first opens and kept for
 *   the page's lifetime.
 */

import "@docsearch/css/dist/style.css";
import "./styles.css";
import { openSearchDatabase, type SearchWorkerClient } from "#search/client.mjs";
import { PLUGIN_NAME, type SearchGlobalData, type SearchResponse } from "#search/common.mjs";
import { search } from "#search/query.mjs";
import { SearchIcon, SearchModal } from "#theme/SearchBar/SearchModal.tsx";

import { useHistory } from "@docusaurus/router";
import { usePluginData } from "@docusaurus/useGlobalData";
import React, { useCallback, useEffect, useRef, useState, useSyncExternalStore } from "react";

function isEditable(target: EventTarget | null): boolean {
    return (
        target instanceof HTMLElement &&
        (target.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName))
    );
}

/**
 * Recently opened hits are kept per reader under this `localStorage` key.
 */
const RECENT_KEY = "authentik.docs-search.recent";

export default function SearchBar() {
    const history = useHistory();
    const { site, indexPath, runtimePath } = usePluginData(PLUGIN_NAME) as SearchGlobalData;
    const [open, setOpen] = useState(false);

    // The server render shows the Control key; the browser reads the platform after hydration.
    const modifier = useSyncExternalStore(
        () => () => {},
        () => (/Mac|iPhone|iPad/.test(globalThis.navigator.platform) ? "⌘" : "Ctrl"),
        () => "Ctrl",
    );

    const database = useRef<Promise<SearchWorkerClient> | null>(null);

    const openDatabase = useCallback((): Promise<SearchWorkerClient> => {
        // A failed open clears the memo so the next open retries.
        const opening =
            database.current ??
            openSearchDatabase(indexPath, runtimePath).catch((error: unknown) => {
                database.current = null;
                throw error;
            });

        database.current = opening;

        return opening;
    }, [indexPath, runtimePath]);

    // The index download starts when the modal opens, so the first query need not wait for it.
    useEffect(() => {
        if (open) {
            openDatabase().catch(() => {});
        }
    }, [open, openDatabase]);

    const runSearch = useCallback(
        async (query: string, signal: AbortSignal): Promise<SearchResponse> => {
            const db = await openDatabase();

            if (signal.aborted) throw new DOMException("aborted", "AbortError");

            return search(db, query, undefined, site);
        },
        [openDatabase, site],
    );

    const navigate = useCallback(
        (href: string) => {
            if (href.startsWith("/")) {
                history.push(href);
            } else {
                globalThis.location.assign(href);
            }
        },
        [history],
    );

    useEffect(() => {
        function onKeyDown(event: KeyboardEvent) {
            const shortcut =
                (event.key.toLowerCase() === "k" && (event.metaKey || event.ctrlKey)) ||
                (event.key === "/" && !isEditable(event.target));

            if (!shortcut) return;

            event.preventDefault();
            setOpen(true);
        }

        globalThis.addEventListener("keydown", onKeyDown);

        return () => globalThis.removeEventListener("keydown", onKeyDown);
    }, []);

    return (
        <>
            <button
                type="button"
                className="DocSearch DocSearch-Button"
                aria-label={`Search (${modifier}+K)`}
                aria-keyshortcuts="Control+K Meta+K /"
                onClick={() => setOpen(true)}
            >
                <span className="DocSearch-Button-Container">
                    <SearchIcon className="DocSearch-Search-Icon" />
                    <span className="DocSearch-Button-Placeholder">Search</span>
                </span>
                <span className="DocSearch-Button-Keys">
                    <kbd className="DocSearch-Button-Key DocSearch-Button-Key--ctrl">
                        {modifier}
                    </kbd>
                    <kbd className="DocSearch-Button-Key">K</kbd>
                </span>
            </button>
            <SearchModal
                open={open}
                site={site}
                onClose={() => setOpen(false)}
                onNavigate={navigate}
                search={runSearch}
                recentKey={RECENT_KEY}
            />
        </>
    );
}
