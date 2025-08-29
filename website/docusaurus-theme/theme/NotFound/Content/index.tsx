import "./styles.css";

import styles from "./styles.module.css";

import { pluckPathnameAffixes, useRedirectEntries } from "#theme/NotFound/Content/utils.ts";

import { RewriteIndex } from "@goauthentik/docusaurus-theme/redirects";

import { Redirect } from "@docusaurus/router";
import Translate from "@docusaurus/Translate";
import Heading from "@theme/Heading";
import type { Props } from "@theme/NotFound/Content";
import clsx from "clsx";
import React, { memo, useEffect, useState } from "react";

const NotFound: React.FC<Props> = ({ className }) => {
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
};

interface RedirectFoundProps extends Props {
    nextURL: string;
}

const RedirectFound: React.FC<RedirectFoundProps> = ({ nextURL, className }) => {
    const usingRouter = nextURL.startsWith("/");

    useEffect(() => {
        console.log("Redirecting...", { nextURL, usingRouter });

        if (usingRouter) return;

        window.location.assign(nextURL);
    }, []);

    return (
        <main
            className={clsx(
                "pending-direct container margin-vert--xl",
                styles.container,
                className,
            )}
        >
            <div className="row">
                <div className={clsx("col col--8 col--offset-2", styles.delayedReveal)}>
                    <Heading as="h1" className="hero__title">
                        <Translate
                            id="theme.NotFound.title"
                            description="The title of the redirect page"
                        >
                            This page has moved
                        </Translate>
                    </Heading>

                    <p>
                        <Translate
                            id="theme.NotFound.p1"
                            description="The first paragraph of the redirect page"
                        >
                            Redirecting...
                        </Translate>
                    </p>

                    <p>
                        <a href={nextURL}>{nextURL}</a>
                    </p>
                    {usingRouter ? <Redirect to={nextURL} /> : null}
                </div>
            </div>
        </main>
    );
};

const NotFoundContentRouter: React.FC<Props> = (props) => {
    const [routeURL, setRouteURL] = useState<URL>();
    const redirects = useRedirectEntries();

    useEffect(() => {
        setRouteURL(new URL(window.location.href));
    }, []);

    if (typeof routeURL === "undefined") {
        return null;
    }

    const rewritesIndex = new RewriteIndex(redirects ?? []);
    const [pathname, suffix] = pluckPathnameAffixes(routeURL);
    const destination = rewritesIndex.finalDestination(pathname);

    // Is there somewhere to redirect to that isn't the current pathname?
    if (!destination || destination === pathname) {
        console.log("No redirect found", { pathname, suffix, destination });

        return <NotFound {...props} />;
    }

    const nextURL = destination + suffix;

    console.log("Redirect found", { pathname, suffix, destination, nextURL });

    document.documentElement.dataset.redirect = "pending";

    return <RedirectFound nextURL={nextURL} {...props} />;
};

export default memo(NotFoundContentRouter);
