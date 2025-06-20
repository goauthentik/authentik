#!/usr/bin/env node
/**
 * @file Memory tracking script for Docusaurus builds.
 */
/* eslint-disable no-console */
// @ts-check
import { exec, spawn } from "node:child_process";
import os from "node:os";
import v8 from "node:v8";
import pidtree from "pidtree";
import pidusage from "pidusage";

/**
 *
 * @param {number} pid
 * @returns {Promise<string | null>}
 */
function getProcessName(pid) {
    return new Promise((resolve) => {
        exec(`ps -p ${pid} -o comm=`, (error, stdout) => {
            if (error) {
                resolve(null);
                return;
            }
            resolve(stdout.trim());
        });
    });
}

/**
 * @param {number} bytes
 * @returns {string}
 */
function gigabytes(bytes) {
    const gb = bytes / 1024 / 1024 / 1024;
    return gb.toFixed(2);
}

/**
 * @param {number} rootPID
 */
async function getProcessMemory(rootPID) {
    const childPIDs = await pidtree(rootPID);

    const allPids = [rootPID, ...childPIDs];

    const stats = await Promise.all(
        allPids.map(async (pid) => {
            const [stats, name] = await Promise.all([
                pidusage(pid).catch(() => null),
                getProcessName(pid).catch(() => null),
            ]);

            if (!stats) return null;

            return {
                ...stats,
                name,
            };
        }),
    );

    return {
        total: stats.reduce((sum, p) => {
            if (!p) return sum;

            return sum + p.memory;
        }, 0),
        stats,
    };
}

const { heap_size_limit } = v8.getHeapStatistics();

const system = {
    total: os.totalmem(),
    free: os.freemem(),
};

/**
 *
 * @param {string} label
 * @param {number} sample
 */
function printComparision(label, sample, total = system.total) {
    const percentage = (sample / total) * 100;

    console.log(`${label}: ${gigabytes(sample)} GB (${percentage.toFixed(2)}%)`);
}

function getSystemMemory() {
    const total = os.totalmem();
    const free = os.freemem();
    const used = total - free;

    return {
        total: gigabytes(total),
        used: gigabytes(used),
        free: gigabytes(free),
        percentUsed: ((used / total) * 100).toFixed(2),
    };
}

function runBuild() {
    if (process.env.NODE_OPTIONS) {
        console.log("Node Options:");
        process.env.NODE_OPTIONS.split(" ").forEach((opt) => {
            if (opt) console.log(`  ${opt}`);
        });
        console.log("");
    }

    console.log("Starting build process with memory tracking...");

    console.log("Initial system memory:");
    const initialMem = getSystemMemory();
    console.log(`  ${initialMem.used} / ${initialMem.total} (${initialMem.percentUsed}% used)`);

    const child = spawn("npm", ["run", "build:all"], {
        stdio: ["inherit", "pipe", "pipe"],
        shell: false,
        env: { ...process.env, FORCE_COLOR: "1" },
    });

    const { pid } = child;

    if (!pid) throw new Error("Build failed to start (no PID)");

    /**
     * @type {PromiseWithResolvers<void>}
     */
    const { resolve, reject, promise } = Promise.withResolvers();

    let sampleCount = 0;

    /**
     * @typedef {Object} MemorySample
     * @property {number} current
     * @property {number} max
     * @property {number} avg
     * @property {number} med
     */

    /**
     * @type {Map<number, MemorySample>}
     */
    const pidSamples = new Map();

    /**
     * @type {Map<number, string>}
     */
    const pidNames = new Map([[process.pid, "main"]]);

    const sample = async () => {
        const { total, stats } = await getProcessMemory(pid);

        if (sampleCount === 0 && total === 0) {
            return;
        }

        sampleCount++;

        for (const stat of stats) {
            if (!stat) continue;

            if (!pidNames.has(stat.pid) && stat.name) {
                pidNames.set(stat.pid, stat.name);
            }

            let sample = pidSamples.get(stat.pid);

            if (!sample) {
                sample = {
                    current: 0,
                    max: 0,
                    avg: 0,
                    med: 0,
                };
                pidSamples.set(stat.pid, sample);
            }

            sample.current = stat.memory;
            sample.max = Math.max(sample.max, stat.memory);
            sample.avg = sample.avg + (stat.memory - sample.avg) / sampleCount;
            sample.med = Math.max(sample.med, sample.avg);
        }
    };

    const sampleInterval = setInterval(sample, 200);

    let peakUsage = 0;

    const logInterval = setInterval(() => {
        const usage = Array.from(pidSamples.values()).reduce((sum, sample) => {
            return sum + sample.current;
        }, 0);

        peakUsage = Math.max(peakUsage, usage);

        console.group(`Sample #${sampleCount}`);

        console.group("V8");

        printComparision("Peak", peakUsage, heap_size_limit);
        printComparision("Peak Delta", peakUsage - heap_size_limit, heap_size_limit);
        printComparision("Usage", usage, heap_size_limit);

        console.groupEnd();

        console.group("System");

        printComparision("Peak", peakUsage);
        printComparision("Peak Delta", peakUsage - system.total);
        printComparision("Usage", usage);
        printComparision("Free", os.freemem());

        console.groupEnd();

        console.groupEnd();
    }, 1000);

    child.stdout.on("data", (d) => {
        process.stdout.write(d);
    });

    child.stderr.on("data", (d) => {
        process.stderr.write(d.toString());
    });

    child.on("exit", (code, signal) => {
        clearInterval(sampleInterval);
        clearInterval(logInterval);

        console.log(`\nBuild exited with code ${code} ${signal ? `(signal: ${signal})` : ""}`);
        if (code === 0) {
            resolve();
        } else {
            reject(new Error(`Build failed with exit code ${code}`));
        }
    });

    child.on("error", (err) => {
        clearInterval(sampleInterval);
        clearInterval(logInterval);

        reject(err);
    });

    return promise;
}

await runBuild()
    .then(() => {
        console.log("\n✅ Build finished successfully.");
        process.exit(0);
    })
    .catch((err) => {
        console.error("\n❌ Build failed:", err.message);
        process.exit(1);
    });
