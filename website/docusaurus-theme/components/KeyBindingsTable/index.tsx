import styles from "./styles.module.css";

export type KeyBindingGroup = [label: React.ReactNode, bindings: KeyBinding[]];

export type KeyBinding = [label: React.ReactNode, key: React.ReactNode];

export interface KeyBindingsTableProps extends React.HTMLAttributes<HTMLTableElement> {
    bindings?: KeyBindingGroup[];
}

export const KeyBindingsTable: React.FC<KeyBindingsTableProps> = ({ bindings = [], ...props }) => {
    return (
        <table className={styles.table} {...props}>
            <thead>
                <tr>
                    <th className={styles.actionColumn} scope="col" id="key-col-action">
                        Action
                    </th>
                    <th className={styles.bindingColumn} scope="col" id="key-col-binding">
                        Key Binding
                    </th>
                </tr>
            </thead>

            {bindings.map(([label, bindings], groupIndex) => (
                <tbody key={groupIndex}>
                    <tr>
                        <th colSpan={2} scope="rowgroup">
                            {label}
                        </th>
                    </tr>
                    {bindings.map(([label, key], bindingIndex) => (
                        <tr key={`${groupIndex}-${bindingIndex}`}>
                            <td>{label}</td>
                            <td>{key}</td>
                        </tr>
                    ))}
                </tbody>
            ))}
        </table>
    );
};
