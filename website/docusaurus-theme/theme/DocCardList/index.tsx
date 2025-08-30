import { type GlossaryItem, isGlossaryPath } from "../utils/glossaryUtils";
import styles from "./styles.module.css";

import type { PropSidebarItem } from "@docusaurus/plugin-content-docs";
import {
    filterDocCardListItems,
    useCurrentSidebarSiblings,
    useDocById,
} from "@docusaurus/plugin-content-docs/client";
import { useLocation } from "@docusaurus/router";
import { usePluginData } from "@docusaurus/useGlobalData";
import DocCard from "@theme/DocCard";
import type { Props } from "@theme/DocCardList";
import clsx from "clsx";
import React, { ComponentType, ReactNode, useEffect, useMemo, useState } from "react";

type SidebarDocLike = PropSidebarItem & { type: "link" };

function isDocLike(it: PropSidebarItem | undefined): it is SidebarDocLike {
    return !!it && it.type === "link";
}

function getStableKey(it: Partial<GlossaryItem & SidebarDocLike>, idx: number) {
    return (it as any).docId ?? (it as any).id ?? (it as any).href ?? (it as any).label ?? idx;
}

function getLabelFromItem(item: PropSidebarItem): string {
    if ("label" in item && typeof item.label === "string") return item.label;
    return "";
}

const labelSorter = (a: PropSidebarItem, b: PropSidebarItem) =>
    getLabelFromItem(a).localeCompare(getLabelFromItem(b), undefined, { sensitivity: "base" });

function DocCardListItem({ item }: { item: React.ComponentProps<typeof DocCard>["item"] }) {
    return (
        <article className={clsx(styles.docCardListItem, "col col--6")}>
            <DocCard item={item} />
        </article>
    );
}

function useDocContent(docId?: string, importsPath?: string) {
    const doc = useDocById(docId);
    // Docusaurus provides the compiled MDX component on `doc.content` for current page only.
    let Content = (doc as any)?.content as ComponentType<any> | null;

    const [Imported, setImported] = useState<ComponentType<any> | null>(null);

    React.useEffect(() => {
        setImported(null);
        if (!docId || Content) return;
        if (!importsPath) return;
        try {
            // eslint-disable-next-line @typescript-eslint/no-var-requires, global-require
            const mod = require("@generated/" + importsPath) as {
                loaders?: Record<string, () => Promise<{ default: ComponentType<any> }>>;
            };
            const loader = mod?.loaders?.[docId];
            if (loader) {
                loader()
                    .then((m) => {
                        if (m?.default) setImported(() => m.default);
                    })
                    .catch(() => {
                        /* ignore */
                    });
            }
        } catch {
            /* ignore */
        }
    }, [docId, importsPath, Content]);

    Content = Content || Imported;
    return { Content, doc };
}

function GlossaryTermCard({ item }: { item: GlossaryItem }) {
    // Try different docId formats
    const docId1 = item?.docId ?? item?.id ?? undefined;
    const docId2 = (item as any)?.docId;
    const docId3 = item?.href?.replace("/docs/", "").replace(/^\//, "");

    const { Content: content1 } = useDocContent(docId1, (item as any).importsPath);
    const { Content: content2 } = useDocContent(docId2, (item as any).importsPath);
    const { Content: content3 } = useDocContent(docId3, (item as any).importsPath);

    const Content = content1 || content2 || content3;

    const [collected, setCollected] = useState<{
        termName: string;
        tags: string[];
        short: React.ReactNode | null;
        long: React.ReactNode | null;
    }>({
        termName: "",
        tags: [],
        short: null,
        long: null,
    });

    const [isContentProcessed, setIsContentProcessed] = useState(false);

    useEffect(() => {
        setCollected({
            termName: "",
            tags: [],
            short: null,
            long: null,
        });
        setIsContentProcessed(false);
    }, [docId1]);

    return (
        <article
            className={clsx(styles.docCardListItem, "col col--12")}
            data-tags={collected.tags.join(",")}
        >
            {Content && !isContentProcessed ? (
                <div style={{ display: "none" }}>
                    {Content ? (
                        <Content
                            components={{
                                TermData: ({
                                    termName,
                                    tags,
                                }: {
                                    termName?: string;
                                    tags?: string[];
                                }) => {
                                    setCollected((prev) => ({
                                        ...prev,
                                        termName:
                                            typeof termName === "string" ? termName : prev.termName,
                                        tags: Array.isArray(tags) ? tags : prev.tags,
                                    }));
                                    return null;
                                },
                                ShortDescription: ({
                                    children,
                                }: {
                                    children?: React.ReactNode;
                                }) => {
                                    setCollected((prev) => ({
                                        ...prev,
                                        short: children ?? null,
                                    }));
                                    return null;
                                },
                                LongDescription: ({ children }: { children?: React.ReactNode }) => {
                                    setCollected((prev) => ({
                                        ...prev,
                                        long: children ?? null,
                                    }));
                                    setIsContentProcessed(true);
                                    return null;
                                },
                            }}
                        />
                    ) : null}
                </div>
            ) : null}

            <div className="card margin-bottom--md">
                <div className="card__header">
                    <h3
                        style={{ backgroundColor: "orange" }}
                        className="margin-vert--sm"
                        aria-label={collected.termName || "Glossary term"}
                    >
                        {collected.termName || "Glossary term"}
                    </h3>
                    {collected.tags?.length ? (
                        <div className="margin-top--xs">
                            {collected.tags.map((t) => (
                                <span key={t} className="badge badge--secondary margin-right--xs">
                                    {t}
                                </span>
                            ))}
                        </div>
                    ) : null}
                </div>
                <div className="card__body">
                    <div
                        style={{ backgroundColor: collected.short ? "pink" : "lightblue" }}
                        className={clsx("glossary__short", {
                            "glossary__short--missing": !collected.short,
                        })}
                    >
                        {collected.short ?? "ShortDescription not provided."}
                    </div>

                    <div
                        style={{ backgroundColor: collected.long ? "purple" : "green" }}
                        className={clsx("glossary__long", {
                            "glossary__long--missing": !collected.long,
                        })}
                    >
                        {collected.long ?? "LongDescription not provided."}
                    </div>
                </div>
            </div>
        </article>
    );
}

export default function DocCardList(props: Props): ReactNode {
    const { items, className } = props;

    const pathname = useLocation()?.pathname ?? "";
    const isGlossary = isGlossaryPath(pathname);

    const glossaryPluginData = usePluginData("ak-glossary-terms-plugin", undefined) as
        | { terms?: { docId: string; label?: string; tags?: string[] }[]; importsPath?: string }
        | undefined;
    if (isGlossary) {
        const count = glossaryPluginData?.terms?.length ?? 0;
        // eslint-disable-next-line no-console
        console.log(`ak-glossary-terms-plugin data in DocCardList: ${count} terms`);
    }

    const siblings = (useCurrentSidebarSiblings() ?? []) as PropSidebarItem[];

    const baseItems = useMemo(
        () => filterDocCardListItems(items ?? siblings),
        [items, siblings],
    ) as PropSidebarItem[];

    const glossaryPool: PropSidebarItem[] = useMemo(() => {
        if (!isGlossary) return baseItems;

        // Prefer plugin-provided list of glossary term docIds
        const terms = glossaryPluginData?.terms ?? [];
        if (terms.length) {
            return terms.map(
                ({ docId, label }) =>
                    ({
                        type: "link",
                        docId,
                        href: `/docs/${docId}`,
                        label: label ?? docId,
                        importsPath: glossaryPluginData?.importsPath,
                    }) as unknown as PropSidebarItem,
            );
        }

        // Fallback: derive from sidebar
        const normalized = (s: string) => s.trim().toLowerCase();
        const termsCat = (items ? [] : baseItems).find((it) => {
            if (!it || it.type !== "category") return false;
            const label = typeof it.label === "string" ? normalized(it.label) : "";
            const href = typeof (it as any).href === "string" ? (it as any).href : "";
            return label === "terms" || href.includes("/glossary/terms") || href.endsWith("/terms");
        }) as any;
        if (termsCat?.items && Array.isArray(termsCat.items)) {
            return filterDocCardListItems(termsCat.items as any[]);
        }
        return baseItems.filter(isDocLike);
    }, [isGlossary, baseItems, items, glossaryPluginData?.terms?.length]);

    const sortedForRender = useMemo(() => {
        if (!isGlossary) return baseItems;
        return [...glossaryPool].sort(labelSorter);
    }, [isGlossary, glossaryPool, baseItems]);

    if (isGlossary) {
        return (
            <section className={clsx("row", className)}>
                {sortedForRender.filter(isDocLike).map((it, idx) => (
                    <GlossaryTermCard key={getStableKey(it as any, idx)} item={it as any} />
                ))}
            </section>
        );
    }

    return (
        <section className={clsx("row", className)}>
            {baseItems.map((item, idx) => (
                <DocCardListItem key={getStableKey(item as any, idx)} item={item as any} />
            ))}
        </section>
    );
}

export { DocCardList };
