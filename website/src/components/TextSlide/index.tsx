import React from "react";
import styles from "./style.module.css";
import clsx from "clsx";

export function TextSlide({ words }) {
    return (
        <div className={clsx(styles.slider)}>
            <div className={clsx(styles.sliderEntry)}>{words[0]}</div>
            <div className={clsx(styles.sliderEntry)}>{words[1]}</div>
            <div className={clsx(styles.sliderEntry)}>{words[2]}</div>
        </div>
    );
}
