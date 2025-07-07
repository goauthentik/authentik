import Link from "@docusaurus/Link";
import Translate from "@docusaurus/Translate";
import Admonition from "@theme/Admonition";
import React, { useCallback, useMemo, useState } from "react";

import styles from "./style.module.css";

type RowID =
    | "replicas"
    | "requests_cpu"
    | "requests_memory"
    | "gunicorn_workers"
    | "gunicorn_threads";

const rows: [rowID: RowID, rowLabel: JSX.Element, units?: string][] = [
    [
        // ---
        "replicas",
        <Translate id="ak.scalingCalculator.replicas">Replicas</Translate>,
    ],
    [
        // ---
        "requests_cpu",
        <Translate id="ak.scalingCalculator.requestsCpu">CPU Requests</Translate>,
    ],
    [
        // ---
        "requests_memory",
        <Translate id="ak.scalingCalculator.requestsMemory">Memory Requests</Translate>,
        "GB",
    ],

    [
        // ---
        "gunicorn_workers",
        <Link to="./configuration#authentik_web__workers">
            <Translate>Gunicorn Workers</Translate>
        </Link>,
    ],
    [
        // ---
        "gunicorn_threads",
        <Link to="./configuration#authentik_web__threads">
            <Translate>Gunicorn Threads</Translate>
        </Link>,
    ],
];

type SetupEstimate = {
    [key in RowID]: number;
};

type SetupEntry = [columnLabel: React.ReactNode, estimate: SetupEstimate];

const FieldName = {
    UserCount: "userCount",
    ConcurrentLogins: "loginCount",
    FlowDuration: "flowDuration",
} as const satisfies Record<string, string>;

type FieldKey = keyof typeof FieldName;
type FieldName = (typeof FieldName)[FieldKey];

type EstimateInput = { [key in FieldName]: number };

type FieldID = `${FieldName}-field`;

const FieldID = Object.fromEntries(
    Object.entries(FieldName).map(([key, value]) => [key, `${value}-field`]),
) as Record<FieldKey, FieldID>;

const SetupComparisionTable: React.FC<EstimateInput> = ({ loginCount }) => {
    const cpuCount = Math.max(1, Math.ceil(loginCount / 10));

    const setups: SetupEntry[] = [
        [
            <Translate
                id="ak.setup.kubernetesRAMOptimized"
                values={{ platform: "Kubernetes", variant: "(RAM Optimized)", separator: <br /> }}
            >
                {"{platform}{separator}{variant}"}
            </Translate>,
            {
                gunicorn_threads: 2,
                gunicorn_workers: 3,
                replicas: Math.max(2, Math.ceil(cpuCount / 2)),
                requests_cpu: 2,
                requests_memory: 1.5,
            },
        ],
        [
            <Translate
                id="ak.setup.kubernetesCPUOptimized"
                values={{ platform: "Kubernetes", variant: "(CPU Optimized)", separator: <br /> }}
            >
                {"{platform}{separator}{variant}"}
            </Translate>,
            {
                gunicorn_threads: 2,
                gunicorn_workers: 2,
                replicas: Math.max(2, cpuCount),
                requests_cpu: 1,
                requests_memory: 1,
            },
        ],
        [
            <Translate
                id="ak.setup.dockerVM"
                values={{
                    platform: "Docker Compose",
                    variant: "(Virtual machine)",
                    separator: <br />,
                }}
            >
                {"{platform}{separator}{variant}"}
            </Translate>,
            {
                gunicorn_threads: 2,
                gunicorn_workers: cpuCount + 1,
                replicas: Math.max(2, cpuCount),
                requests_cpu: cpuCount,
                requests_memory: cpuCount,
            },
        ],
    ];

    return (
        <Admonition type="tip" icon={null} title={null} className={styles.admonitionTable}>
            <div
                className={styles.comparisionTable}
                style={
                    { "--ak-comparision-table-columns": setups.length + 1 } as React.CSSProperties
                }
            >
                <header>
                    <div className={styles.columnLabel}>
                        <Translate id="ak.scalingCalculator.server">Resources</Translate>
                    </div>
                    {setups.map(([columnLabel], i) => (
                        <div className={styles.columnLabel} key={i}>
                            {columnLabel}
                        </div>
                    ))}
                </header>

                {rows.map(([rowID, rowLabel, units]) => {
                    return (
                        <section key={rowID}>
                            <div className={styles.rowLabel}>{rowLabel}</div>

                            {setups.map(([_rowLabel, estimate], i) => {
                                const estimateValue = estimate[rowID] || "N/A";

                                return (
                                    <div className={styles.fieldValue} key={i}>
                                        <Translate
                                            id={`ak.scalingCalculator.${rowID}`}
                                            values={{
                                                value: estimateValue,
                                                units: units ? ` ${units}` : "",
                                            }}
                                        >
                                            {"{value}{units}"}
                                        </Translate>
                                    </div>
                                );
                            })}
                        </section>
                    );
                })}
            </div>
        </Admonition>
    );
};

export const DatabaseEstimateTable: React.FC<EstimateInput> = ({ loginCount, userCount }) => {
    const cpuCount = Math.max(1, Math.ceil(loginCount / 10));

    const postgres = {
        cpus: Math.max(2, cpuCount / 4),
        ram: Math.max(4, cpuCount),
        storage_gb: Math.ceil(userCount / 25000),
    };

    const redis = {
        cpus: Math.max(2, cpuCount / 4),
        ram: Math.max(2, cpuCount / 2),
    };

    return (
        <Admonition type="tip" icon={null} title={null} className={styles.admonitionTable}>
            <div
                className={styles.comparisionTable}
                style={{ "--ak-comparision-table-columns": 3 } as React.CSSProperties}
            >
                <header>
                    <div className={styles.columnLabel}>
                        <Translate id="ak.scalingCalculator.server">Resources</Translate>
                    </div>
                    <div className={styles.columnLabel}>PostgreSQL</div>
                    <div className={styles.columnLabel}>Redis</div>
                </header>

                <section>
                    <div className={styles.rowLabel}>CPUs</div>
                    <div className={styles.fieldValue}>{postgres.cpus}</div>
                    <div className={styles.fieldValue}>{redis.cpus}</div>
                </section>

                <section>
                    <div className={styles.rowLabel}>Memory</div>
                    <div className={styles.fieldValue}>{postgres.ram} GB</div>
                    <div className={styles.fieldValue}>{redis.ram} GB</div>
                </section>

                <section>
                    <div className={styles.rowLabel}>Storage</div>
                    <div className={styles.fieldValue}>{postgres.storage_gb} GB</div>
                    <div className={styles.fieldValue}>
                        <Translate id="ak.scalingCalculator.varies">Varies</Translate>
                    </div>
                    <div />
                </section>
            </div>
        </Admonition>
    );
};

export const ScalingCalculator: React.FC = () => {
    const [estimateInput, setEstimateInput] = useState<EstimateInput>(() => {
        const userCount = 100;
        const flowDuration = 15;

        return {
            userCount,
            flowDuration,
            loginCount: -1,
        };
    });

    const estimatedLoginCount = useMemo(() => {
        const { userCount, flowDuration } = estimateInput;

        // if (loginCount > 0) return loginCount;

        // Assumption that users log in over a period of 15 minutes.
        return Math.ceil(userCount / 15.0 / 60.0) * flowDuration;
    }, [estimateInput]);

    const estimatedLoginValue = estimateInput[FieldName.ConcurrentLogins];

    const handleFieldChange = useCallback<React.ChangeEventHandler<HTMLInputElement>>((event) => {
        const { name, value } = event.target;
        const nextFieldValue = value.length ? parseInt(value, 10) : -1;

        setEstimateInput((currentEstimate) => ({
            ...currentEstimate,
            [name as FieldName]: nextFieldValue,
        }));
    }, []);

    return (
        <>
            <h3>
                <Translate id="ak.scalingCalculator.usageEstimates">Usage Estimates</Translate>
            </h3>

            <Admonition type="info" icon={null} title={null}>
                <form className={styles.admonitionForm} autoComplete="off">
                    <div className={styles.labelGroup}>
                        <label htmlFor={FieldID.UserCount}>
                            <Translate id="ak.scalingCalculator.activeUsersLabel">
                                Active Users
                            </Translate>
                        </label>

                        <p>
                            <Translate id="ak.scalingCalculator.activeUsersDescription">
                                This is used to calculate database storage, and estimate how many
                                concurrent logins you can expect.
                            </Translate>
                        </p>
                    </div>

                    <div className={styles.field}>
                        <input
                            id={FieldID.UserCount}
                            type="number"
                            step="10"
                            name={FieldName.UserCount}
                            value={estimateInput[FieldName.UserCount]}
                            onChange={handleFieldChange}
                            required
                            min={1}
                        />
                    </div>

                    <div className={styles.labelGroup}>
                        <label htmlFor={FieldID.FlowDuration}>
                            <Translate id="ak.scalingCalculator.flowDurationLabel">
                                Flow Duration
                            </Translate>
                        </label>

                        <p>
                            <Translate id="ak.scalingCalculator.flowDurationDescription">
                                A single login may take several seconds for the user to enter their
                                password, MFA method, etc. If you know what usage pattern to expect,
                                you can override that value from the computed one.
                            </Translate>
                        </p>
                    </div>

                    <div className={styles.field}>
                        <input
                            id={FieldID.FlowDuration}
                            type="number"
                            step="5"
                            name={FieldName.FlowDuration}
                            value={estimateInput[FieldName.FlowDuration]}
                            onChange={handleFieldChange}
                            min={0}
                        />
                    </div>
                    <div className={styles.labelGroup}>
                        <label htmlFor={FieldID.ConcurrentLogins}>
                            <Translate id="ak.scalingCalculator.concurrentLoginsLabel">
                                Concurrent Logins
                            </Translate>
                        </label>

                        <p>
                            <Translate id="ak.scalingCalculator.concurrentLoginsDescription">
                                We estimate that all of the users will log in over a period of 15
                                minutes, greatly reducing the load on the instance.
                            </Translate>
                        </p>
                    </div>

                    <div className={styles.field}>
                        <input
                            id={FieldID.ConcurrentLogins}
                            type="number"
                            step="10"
                            name={FieldName.ConcurrentLogins}
                            placeholder={estimatedLoginCount.toString()}
                            value={estimatedLoginValue === -1 ? "" : estimatedLoginValue.toString()}
                            onChange={handleFieldChange}
                            min={0}
                        />
                    </div>
                </form>
            </Admonition>

            <h3>
                <Translate id="ak.scalingCalculator.deploymentConfigurations">
                    Deployment Configurations
                </Translate>
            </h3>

            <SetupComparisionTable {...estimateInput} />

            <h3>
                <Translate id="ak.scalingCalculator.DatabaseConfigurations">
                    Database Configurations
                </Translate>
            </h3>

            <DatabaseEstimateTable {...estimateInput} />
        </>
    );
};

export default ScalingCalculator;
