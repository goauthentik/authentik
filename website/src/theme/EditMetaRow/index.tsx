import React, { type ReactNode } from "react";
import clsx from "clsx";
import EditThisPage from "@theme/EditThisPage";
import type { Props } from "@theme/EditMetaRow";

import LastUpdated from "@theme/LastUpdated";
import Admonition from "@theme/Admonition";
import styles from "./styles.module.css";
import Translate from "@docusaurus/Translate";
import IconNote from "@theme/Admonition/Icon/Note";

const EditMetaRow: React.FC<Props> = ({
    className,
    editUrl,
    lastUpdatedAt,
    lastUpdatedBy,
}: Props) => {
    return (
        <>
            <hr className={styles.divider} />

            <Admonition
                className={clsx(styles.admonitionContrib, className)}
                icon={<IconNote className={styles.contribIcon} />}
                title={
                    <span className={styles.headerContent}>
                        Help us improve this content
                    </span>
                }
                type="info"
            >
                <p>
                    <Translate
                        id="theme.common.contributor.footerDescription1"
                        description="The initial description for the contribution footer"
                    >
                        Documentation for authentik is made possible by
                        contributors like you!
                    </Translate>
                </p>

                <p>
                    <Translate
                        id="theme.common.contributor.footerDescription2"
                        description="The initial description for the contribution footer"
                    >
                        You can help us improve this page, or let us know about
                        an issue by opening a pull request on GitHub.
                    </Translate>
                </p>

                <div className="row">
                    <div className="col col--12">
                        <ul>
                            {editUrl && (
                                <li>
                                    <EditThisPage editUrl={editUrl} />
                                </li>
                            )}

                            <li>
                                <a
                                    href="https://docs.goauthentik.io/docs/developer-docs/"
                                    target="_blank"
                                    rel="noreferrer noopener"
                                >
                                    <Translate
                                        id="theme.common.contributor.howToContribute"
                                        description="The link label to the contribution guide"
                                    >
                                        Contributor Guide
                                    </Translate>
                                </a>
                            </li>

                            <li>
                                <a
                                    href="https://github.com/goauthentik/authentik/issues/new/choose"
                                    target="_blank"
                                    rel="noreferrer noopener"
                                >
                                    <Translate
                                        id="theme.common.contributor.createAnIssue"
                                        description="The link label to report a documentation issue"
                                    >
                                        Open an issue
                                    </Translate>
                                </a>
                            </li>

                            <li>
                                <a
                                    href="https://goauthentik.io/pricing/"
                                    target="_blank"
                                    rel="noreferrer noopener"
                                >
                                    <Translate
                                        id="theme.common.contributor.getSupport"
                                        description="The link label to request support"
                                    >
                                        Get Enterprise Support
                                    </Translate>
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>
            </Admonition>

            <div className="row">
                <div className={clsx("col", styles.lastUpdated)}>
                    {(lastUpdatedAt || lastUpdatedBy) && (
                        <LastUpdated
                            lastUpdatedAt={lastUpdatedAt}
                            lastUpdatedBy={lastUpdatedBy}
                        />
                    )}
                </div>
            </div>
        </>
    );
};

export default EditMetaRow;
