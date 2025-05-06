import React, { ReactNode } from "react";
import styles from "./cards.module.css";

export interface CardProps {
    title: string;
    icon?: string;
    children: ReactNode;
}

export const Card: React.FC<CardProps> = ({ title, icon = "", children }) => {
    return (
        <div className={styles.card}>
            <div className={styles.cardHeader}>
                <h3>
                    {icon && <span className={styles.cardIcon}>{icon}</span>}
                    {title}
                </h3>
            </div>
            <div className={styles.cardBody}>
                {children}
            </div>
        </div>
    );
};

export interface CardGridProps {
    children: ReactNode;
}

export const CardGrid: React.FC<CardGridProps> = ({ children }) => {
    return (
        <div className={styles.cardGrid}>
            {children}
        </div>
    );
};

export default Card; 