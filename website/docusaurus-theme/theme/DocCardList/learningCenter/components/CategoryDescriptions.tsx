import commonStyles from "../../../../components/LearningCenter/styling/common.module.css";
import { getCategoryDescription } from "../../../utils/learningCenter/categoryDescriptions";

interface CategoryDescriptionsProps {
    selectedCategories: string[];
}

export default function CategoryDescriptions({ selectedCategories }: CategoryDescriptionsProps) {
    if (selectedCategories.length === 0) {
        return null;
    }

    return (
        <div className={commonStyles.categoryDescriptions}>
            {selectedCategories.map((category) => (
                <p key={category} className={commonStyles.categoryDescriptionText}>
                    <strong>{category}</strong>: {getCategoryDescription(category)}
                </p>
            ))}
        </div>
    );
}
