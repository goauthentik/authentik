/**
 * No-op for SSG so MDX can render at build time.
 * In the DocCardList, you locally override this via `components={{ TermData: ... }}` to collect termName/tags.
 */
export default function TermData(_: { termName?: string; tags?: string[] }) {
    return null;
}
