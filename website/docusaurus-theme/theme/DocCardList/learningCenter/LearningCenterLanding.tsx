import LearningPaths from "../../../components/LearningCenter/LearningPaths";
import type { LearningPathDef } from "../../../components/LearningCenter/learningPathsConfig";
import commonStyles from "../../../components/LearningCenter/styling/common.module.css";
import landingStyles from "../../../components/LearningCenter/styling/landing.module.css";
import {
    type DifficultyLevel,
    extractAvailableCategories,
    extractAvailableDifficulties,
    type LearningCenterResource,
} from "../../utils/learningCenter/utils";
import LandingAllArticlesCta from "./components/LandingAllArticlesCta";
import LandingFilterPanel from "./components/LandingFilterPanel";
import { writeLearningCenterNavigationState } from "./navigationState";

import type { ReactNode } from "react";
import { useCallback, useMemo, useState } from "react";

interface LearningCenterLandingProps {
    resources: LearningCenterResource[];
    learningPaths: LearningPathDef[];
}

const ARTICLES_PAGE_PATH = "/core/learning-center/articles/";

export default function LearningCenterLanding({
    resources,
    learningPaths,
}: LearningCenterLandingProps): ReactNode {
    const intro =
        "Start with a curated path, or use one of the alternatives below to find exactly what you need.";
    const primaryText =
        "Learning paths are the easiest way to progress with context and a clear order.";
    const filterText =
        "Need something specific? Search by keyword, then narrow by category or experience level.";
    const allArticlesText = "Or browse everything:";

    const [searchValue, setSearchValue] = useState("");
    const availableCategories = useMemo(() => extractAvailableCategories(resources), [resources]);
    const availableDifficulties = useMemo(
        () => extractAvailableDifficulties(resources),
        [resources],
    );

    const navigateWithState = useCallback(
        (state: {
            filter?: string;
            categories?: string[];
            difficulty?: DifficultyLevel | null;
        }) => {
            writeLearningCenterNavigationState(state);
            window.location.assign(ARTICLES_PAGE_PATH);
        },
        [],
    );

    return (
        <div className={commonStyles.learningCenter}>
            <section className={landingStyles.discoveryIntro}>
                <h2 className={landingStyles.discoveryTitle}>Learning Center</h2>
                <p className={landingStyles.discoveryDescription}>{intro}</p>
            </section>

            <section className={landingStyles.discoveryPrimary}>
                <h3 className={landingStyles.discoverySubTitle}>Learning paths</h3>
                <p className={landingStyles.discoveryMethodBody}>{primaryText}</p>
                <LearningPaths paths={learningPaths} resources={resources} hideTitle />
            </section>

            <section className={landingStyles.discoveryAlternatives}>
                <p className={landingStyles.discoveryKicker}>Looking for something specific?</p>
                <article className={landingStyles.discoveryOptionCard}>
                    <h3 className={landingStyles.discoveryOptionTitle}>Filter articles</h3>
                    <p className={landingStyles.discoveryMethodBody}>{filterText}</p>
                    <LandingFilterPanel
                        searchValue={searchValue}
                        setSearchValue={setSearchValue}
                        availableCategories={availableCategories}
                        availableDifficulties={availableDifficulties}
                        onNavigate={navigateWithState}
                    />
                </article>

                <LandingAllArticlesCta to={ARTICLES_PAGE_PATH} text={allArticlesText} />
            </section>
        </div>
    );
}
