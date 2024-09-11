import React from "react";
import { useDocsSidebar } from "@docusaurus/plugin-content-docs/client";
import {
    PropSidebar,
    PropSidebarItem,
    PropSidebarItemLink,
} from "@docusaurus/plugin-content-docs";
import clsx from "clsx";
import DocCard from "@theme/DocCard";

type Sidebar = { name: string; items: PropSidebar };

function getAllIntegrations() {
    const sidebar = useDocsSidebar() as unknown as Sidebar;
    const items: PropSidebarItemLink[] = [];
    const ignoredUrls = ["/integrations/", "/integrations/services/"];
    const walker = (root: PropSidebarItem[]) => {
        root.forEach((item) => {
            if (item.type === "category") {
                walker(item.items);
            } else if (item.type === "link") {
                if (ignoredUrls.includes(item.href)) {
                    return;
                }
                items.push(item);
            }
        });
    };
    walker(sidebar.items);
    return items.sort((a, b) => {
        if (a.label < b.label) return -1;
        if (a.label > b.label) return 1;
        return 0;
    });
}

function IntegrationsPage() {
    const integrations = getAllIntegrations();
    return (
        <>
            <section className={clsx("row")}>
                {integrations.map((item, index) => (
                    <article
                        key={index}
                        className="col col--4 margin-bottom--lg"
                    >
                        <DocCard item={item} />
                    </article>
                ))}
            </section>
        </>
    );
}

export default IntegrationsPage;
