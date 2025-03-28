import React from "react";

export interface MDXWrapperProps {
    children: React.ReactNode;
    frontmatter: Record<string, string>;
}

/**
 * A wrapper component for MDX content that adds a title if one is provided in the frontmatter.
 */
export const MDXWrapper: React.FC<MDXWrapperProps> = ({ children, frontmatter }) => {
    const { title } = frontmatter;
    const nextChildren = React.Children.toArray(children);

    if (title) {
        nextChildren.unshift(<h1 key="header-title">{title}</h1>);
    }

    return <>{nextChildren}</>;
};
