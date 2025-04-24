import styles from "./styles.module.css";

const RADIUSProtocols = [
    "PAP",
    "CHAP",
    "Digest",
    "MS-CHAP",
    "PEAP",
    "MS-CHAPv2",
    "Cisco LEAP",
    "EAP-GTC",
    "EAP-MD5",
    "EAP-PWD",
] as const satisfies string[];

type RADIUSProtocol = (typeof RADIUSProtocols)[number];

const HashKinds = [
    "Cleartext",
    "NT",
    "MD5",
    "Salted MD5",
    "SHA1",
    "Salted SHA1",
    "Unix Crypt",
] as const satisfies string[];

type HashKind = (typeof HashKinds)[number];

const supportMatrix: Record<HashKind, RADIUSProtocol[]> = {
    "Cleartext": [
        "PAP",
        "CHAP",
        "Digest",
        "MS-CHAP",
        "PEAP",
        "MS-CHAPv2",
        "Cisco LEAP",
        "EAP-GTC",
        "EAP-MD5",
        "EAP-PWD",
    ],
    "NT": ["PAP", "MS-CHAP", "PEAP", "MS-CHAPv2", "Cisco LEAP", "EAP-GTC"],
    "MD5": ["PAP", "EAP-GTC"],
    "Salted MD5": ["PAP", "EAP-GTC"],
    "SHA1": ["PAP", "EAP-GTC"],
    "Salted SHA1": ["PAP", "EAP-GTC", "EAP-PWD"],
    "Unix Crypt": ["PAP", "EAP-GTC", "EAP-PWD"],
};

export const HashSupport: React.FC = () => {
    return (
        <table className={styles.table}>
            <thead>
                <tr>
                    <th></th>
                    {HashKinds.map((hashKind, i) => (
                        <th key={i}>{hashKind}</th>
                    ))}
                </tr>
            </thead>

            <tbody>
                {RADIUSProtocols.map((radiusProtocol, i) => (
                    <tr key={i}>
                        <td>{radiusProtocol}</td>
                        {HashKinds.map((hashKind) => {
                            const protocols = supportMatrix[hashKind];
                            const supported = protocols.includes(radiusProtocol);

                            return (
                                <td data-supported={supported} key={hashKind}>
                                    {supported ? "✓" : "✗"}
                                </td>
                            );
                        })}
                    </tr>
                ))}
            </tbody>
        </table>
    );
};
