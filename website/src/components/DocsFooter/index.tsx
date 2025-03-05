import Link from "@docusaurus/Link";

import styles from "./styles.module.css";
import { useDoc } from "@docusaurus/plugin-content-docs/client";

export function DocsFooterEdit() {
    const ctx = useDoc();
    let sourceUrl = ctx.metadata.editUrl;

    return (
        <div className={styles.cta}>
            <div className="card">
                <div className="card__header">
                    <strong>Help improve this content</strong>
                </div>
                <div className="card__body">
                    Docs are great yay
                </div>
                <div className="card__footer">
                    <div className="container container--fluid">
                        <div className="footer__links">
                            <Link
                                className="footer__link-item"
                                href="https://docs.goauthentik.io/docs/developer-docs/"
                            >
                                How to contribute
                            </Link>
                            <span className="footer__link-separator">
                                &middot;
                            </span>
                            <Link
                                className="footer__link-item"
                                href={sourceUrl}
                            >
                                Edit this page
                            </Link>
                            <span className="footer__link-separator">
                                &middot;
                            </span>
                            <Link
                                className="footer__link-item"
                                href="https://github.com/goauthentik/authentik/issues/new/choose"
                            >
                                Create an issue
                            </Link>
                            <span className="footer__link-separator">
                                &middot;
                            </span>
                            <Link
                                className="footer__link-item"
                                href="http://customers.goauthentik.io/l/support"
                            >
                                Get support
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
