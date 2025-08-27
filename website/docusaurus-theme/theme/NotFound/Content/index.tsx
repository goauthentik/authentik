import styles from "./styles.module.css";

import { Redirect } from "@docusaurus/router";
import Translate from "@docusaurus/Translate";
import Heading from "@theme/Heading";
import type { Props } from "@theme/NotFound/Content";
import clsx from "clsx";
import React, { type ReactNode, useEffect, useState } from "react";

const DocsPrefix = "/docs";

export default function NotFoundContent({ className }: Props): ReactNode {
    const [routeURL, setRouteURL] = useState<URL>();

    useEffect(() => {
        setRouteURL(new URL(window.location.href));
    }, []);

    if (typeof routeURL === "undefined") {
        return null;
    }

    if (routeURL.pathname.startsWith(DocsPrefix)) {
        routeURL.pathname = routeURL.pathname.slice(DocsPrefix.length);
        const [, fullPathname = ""] = routeURL.href.split(window.location.origin);

        return <Redirect to={fullPathname} />;
    }

    return (
        <main className={clsx("container margin-vert--xl", styles.container, className)}>
            <div className="row">
                <div className="col col--8 col--offset-2">
                    <Heading as="h1" className="hero__title">
                        <Translate
                            id="theme.NotFound.title"
                            description="The title of the 404 page"
                        >
                            Page not found
                        </Translate>
                    </Heading>
                    <p>
                        <Translate
                            id="theme.NotFound.p1"
                            description="The first paragraph of the 404 page"
                        >
                            The page you are looking for may have moved or been deleted. Try using
                            the search bar above to find what you are looking for.
                        </Translate>
                    </p>
                </div>
            </div>
        </main>
    );
}
