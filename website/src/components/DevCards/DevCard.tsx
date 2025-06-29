import React, { ReactNode } from "react";
import styles from "./DevCard.module.css";

export interface DevCardProps {
    title: string;
    description?: string;
    icon?: string;
    children?: ReactNode;
    to?: string;
    badge?: string;
    badgeColor?: 'primary' | 'success' | 'info' | 'warning';
}

export const DevCard: React.FC<DevCardProps> = ({ 
    title, 
    description, 
    icon, 
    children, 
    to,
    badge,
    badgeColor = 'primary'
}) => {
    const badgeClass = badge ? `${styles.badge} ${styles[`badge${badgeColor.charAt(0).toUpperCase() + badgeColor.slice(1)}`]}` : '';
    
    const CardContent = () => (
        <>
            <div className={styles.cardHeader}>
                <h3>
                    {icon && <span className={styles.cardIcon} aria-hidden="true">{icon}</span>}
                    {title}
                    {badge && <span className={badgeClass}>{badge}</span>}
                </h3>
            </div>
            <div className={styles.cardBody}>
                {description && <p className={styles.cardDescription}>{description}</p>}
                {children}
            </div>
            {to && <div className={styles.cardFooter}>
                <span className={styles.learnMore}>Learn more</span>
            </div>}
        </>
    );

    if (to) {
        return (
            <a 
                href={to} 
                className={styles.cardLink}
                aria-label={`Learn more about ${title}`}
            >
                <div className={styles.card}>
                    <CardContent />
                </div>
            </a>
        );
    }

    return (
        <div className={styles.card}>
            <CardContent />
        </div>
    );
};

export interface DevCardGridProps {
    children: ReactNode;
    columns?: 1 | 2 | 3 | 4;
}

export const DevCardGrid: React.FC<DevCardGridProps> = ({ children, columns = 3 }) => {
    return (
        <div className={`${styles.cardGrid} ${styles[`columns${columns}`]}`}>
            {children}
        </div>
    );
};

export default DevCard; 