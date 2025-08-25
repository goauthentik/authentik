import React, {type ComponentProps, type ReactNode} from 'react';
import clsx from 'clsx';
import {
  useCurrentSidebarSiblings,
  filterDocCardListItems,
  useDocById,
} from '@docusaurus/plugin-content-docs/client';
import {useLocation} from '@docusaurus/router';
import type {PropSidebarItem} from '@docusaurus/plugin-content-docs';
import registry from '@generated/registry';
import DocCard from '@theme/DocCard';
import type {Props} from '@theme/DocCardList';
import styles from './styles.module.css';

function DocCardListForCurrentSidebarCategory({className}: Props) {
  const items = useCurrentSidebarSiblings();
  return <DocCardList items={items} className={className} />;
}

function DocCardListItem({
  item,
}: {
  item: ComponentProps<typeof DocCard>['item'];
}) {
  return (
    <article className={clsx(styles.docCardListItem, 'col col--6')}>
      <DocCard item={item} />
    </article>
  );
}

// lol look at all the | undefined's the any's and the || s
function GlossaryTermCard({item}: {item: any}) {
  const docId = (item && (item.docId || item.id)) as string | undefined;
  const doc: any = (useDocById as any)(docId ?? '');
  const Content = doc?.content as React.ComponentType<any> | undefined;
  const fm = (doc && (doc.frontMatter || doc.metadata?.frontMatter)) || {};

  const [dynContent, setDynContent] = React.useState<React.ComponentType<any> | undefined>(undefined);
  const [dynFM, setDynFM] = React.useState<any>(undefined);

  React.useEffect(() => {
    if (Content) return;
    if (!docId) return;
    const candidates = [
      `@site/${docId}.mdx`,
      `@site/${docId}.md`,
    ];
    let loader: (() => Promise<any>) | undefined;
    for (const modPath of candidates) {
      const match = Object.values<any>(registry).find((e: any) => e && e[1] === modPath);
      if (match) {
        loader = match[0] as () => Promise<any>;
        break;
      }
    }
    if (!loader) {
      console.debug('[DocCardList] No registry entry for docId', docId);
      return;
    }
    let cancelled = false;
    loader()
      .then((mod) => {
        if (cancelled) return;
        const Comp = (mod && (mod.default || (mod as any).MDXContent)) as React.ComponentType<any> | undefined;
        setDynContent(Comp);
        setDynFM((mod && (mod.frontMatter || (mod as any).metadata?.frontMatter)) ?? undefined);
      })
      .catch((e) => {
        if (cancelled) return;
        console.error('[DocCardList] Failed to load MDX module from registry', {docId, error: e});
      });
    return () => {
      cancelled = true;
    };
  }, [docId, Content]);

  const termName: string =
    (dynFM && (dynFM as any).termName) ||
    (fm.termName as string) ||
    item?.label ||
    doc?.metadata?.title ||
    '';
  const tags: string[] = (dynFM?.tags as string[]) || (fm.tags as string[]) || (doc?.metadata?.tags as string[]) || [];

  debugger;
  console.debug('[DocCardList] render GlossaryTermCard', {docId, termName, tagCount: tags.length});

  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const [hasShort, setHasShort] = React.useState(false);
  const [hasLong, setHasLong] = React.useState(false);
  React.useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    setHasShort(!!el.querySelector('.glossary__short'));
    setHasLong(!!el.querySelector('.glossary__long'));
  }, [docId, dynContent, Content]);

  const renderContent = () => {
    try {
      const ActiveContent = Content || dynContent;
      if (!ActiveContent) {
        console.error('[DocCardList] Unable to load MDX content for glossary term', {docId, item, doc});
        return (
          <>
            {doc && typeof (doc as any).description === 'string' && (doc as any).description.length > 0 ? (
              <div className="glossary__short">{(doc as any).description}</div>
            ) : null}
          </>
        );
      }
      return (
        <ActiveContent
          components={{
            ShortDescription: ({children}: any) => (
              <div className="glossary__short">{children}</div>
            ),
            LongDescription: ({children}: any) => (
              <div className="glossary__long">{children}</div>
            ),
          }}
        />
      );
    } catch (e) {
      console.error('[DocCardList] Error rendering glossary term content', {docId, termName, error: e});
      return <p>Unable to render content.</p>;
    }
  };

  return (
    <article className={clsx(styles.docCardListItem, 'col col--12')} data-tags={(tags || []).join(',')}>
      <div className="card margin-bottom--md">
        <div className="card__header">
          <h3 className="margin-vert--sm">{termName}</h3>
        </div>
        <div className="card__body" ref={containerRef as any}>
          {renderContent()}
          {!hasShort && (
            <div className="glossary__short glossary__short--missing">ShortDescription not provided.</div>
          )}
          {!hasLong && (
            <div className="glossary__long glossary__long--missing">LongDescription not provided.</div>
          )}
        </div>
      </div>
    </article>
  );
}


export default function DocCardList(props: Props): ReactNode {
  const {items, className} = props;
  const location = useLocation();
  const pathname = location?.pathname ?? '';

  const isGlossary = /\/glossary(\/|$)/.test(pathname); // wasn't there a better way Teffen showed me? Should have noted it down
    debugger;
    console.debug('[DocCardList] pathname:', pathname, 'isGlossary:', isGlossary);

  if (!items) {
    const siblings = (useCurrentSidebarSiblings() ?? []) as PropSidebarItem[];
    const filtered: PropSidebarItem[] = filterDocCardListItems(siblings) as unknown as PropSidebarItem[];
    debugger;
    console.debug('[DocCardList] children count:', filtered.length);

    if (isGlossary) {
      // Find a `terms` category among siblings and inline-render each term card.
      const termsCat: any = filtered.find((it: any) => {
        if (!it || it.type !== 'category') return false;
        const label = typeof it.label === 'string' ? it.label.toLowerCase() : '';
        const href = typeof it.href === 'string' ? it.href : '';
        return label === 'terms' || href.includes('/glossary/terms') || href.endsWith('/terms'); // this is questionable
      });
      debugger;
      console.debug('[DocCardList] glossary termsCat found:', Boolean(termsCat));
      if (termsCat && Array.isArray(termsCat.items)) {
        const nested = filterDocCardListItems(termsCat.items as any) as any[];
        debugger;
        console.debug('[DocCardList] inline term cards, count:', nested.length);
        const sorted = [...nested].sort((a: any, b: any) =>
          String(a?.label || '').localeCompare(String(b?.label || ''), undefined, {sensitivity: 'base'})
        );
        return (
          <section className={clsx('row', className)}>
            {sorted
              .filter((it: any) => it && (it.type === 'doc' || it.type === 'ref' || it.type === 'link'))
              .map((it: any, idx: number) => (
                <GlossaryTermCard key={idx} item={it} />
              ))}
          </section>
        );
      }
    }

    // Default rendering
    return (
      <section className={clsx('row', className)}>
        {filtered.map((item, index) => (
          <DocCardListItem key={index} item={item} />
        ))}
      </section>
    );
  }

  const filteredItems = filterDocCardListItems(items);
  debugger;
  return (
    <section className={clsx('row', className)}>
      {filteredItems.map((item, index) => (
        <DocCardListItem key={index} item={item} />
      ))}
    </section>
  );
}

export { DocCardList };
