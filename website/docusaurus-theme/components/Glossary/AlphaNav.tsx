import styles from "./styles.module.css";

import React from "react";

/** A–Z navigation anchors for simplified view. */
export interface AlphaNavProps {
    letters: string[];
}

export const AlphaNav: React.FC<AlphaNavProps> = ({ letters }) => {
    if (letters.length === 0) return null;
    return (
        <nav className={styles.alphaNav} aria-label="A to Z navigation">
            {letters.map((letter) => (
                <a key={letter} href={`#letter-${letter}`} className={styles.alphaNavLink}>
                    {letter}
                </a>
            ))}
        </nav>
    );
};

export default AlphaNav;
