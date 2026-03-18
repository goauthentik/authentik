import commonStyles from "../../../../components/LearningCenter/styling/common.module.css";

export default function NoResults() {
    return (
        <div className={commonStyles.noResults}>
            <p>No resources match your filter criteria.</p>
        </div>
    );
}
