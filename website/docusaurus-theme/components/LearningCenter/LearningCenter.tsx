import styles from "./styles.module.css";

import Link from "@docusaurus/Link";
import clsx from "clsx";
import React from "react";

export interface SectionLink {
    title: string;
    url: string;
}

export interface Section {
    title: string;
    description: string;
    links: SectionLink[];
}

export interface LearningCenterProps {
    title?: string;
    description?: string;
    sections: Section[];
    className?: string;
}

export const LearningCenter: React.FC<LearningCenterProps> = ({
    title,
    description,
    sections,
    className,
}) => {
    return (
        <div className={clsx(styles.learningCenter, className)}>
            {(title || description) && (
                <div className={styles.header}>
                    {title && <h2 className={styles.title}>{title}</h2>}
                    {description && <p className={styles.description}>{description}</p>}
                </div>
            )}

            <div className={styles.sectionGrid}>
                {sections.map((section, idx) => (
                    <div key={idx} className={styles.sectionCard}>
                        <div className={styles.sectionContent}>
                            <h3 className={styles.sectionTitle}>{section.title}</h3>
                            <p className={styles.sectionDescription}>{section.description}</p>
                        </div>
                        {section.links && section.links.length > 0 && (
                            <div className={styles.sectionLinks}>
                                {section.links.map((link, linkIdx) => (
                                    <Link
                                        key={linkIdx}
                                        to={link.url}
                                        className={styles.sectionLink}
                                    >
                                        <i className="fa fa-arrow-right"></i>
                                        <span>{link.title}</span>
                                    </Link>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default LearningCenter;
