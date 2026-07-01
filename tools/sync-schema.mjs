import {createHash} from "node:crypto";
import {mkdir, writeFile} from "node:fs/promises";
import {join} from "node:path";

const upstreamRef = process.env.MAA_SCHEMA_REF ?? "main";
const targetDir = process.env.MAA_SCHEMA_TARGET ?? "deps/tools";
const downloadAttempts = Number.parseInt(process.env.MAA_SCHEMA_DOWNLOAD_ATTEMPTS ?? "4", 10);
const baseUrls = (
    process.env.MAA_SCHEMA_BASE_URLS ??
    [
        `https://raw.githubusercontent.com/MaaXYZ/MaaFramework/${upstreamRef}/tools`,
        `https://cdn.jsdelivr.net/gh/MaaXYZ/MaaFramework@${upstreamRef}/tools`,
    ].join(",")
)
    .split(",")
    .map((url) => url.trim().replace(/\/$/u, ""))
    .filter(Boolean);

const upstreamSchemas = [
    {
        path: "interface.schema.json",
        validate: (json) => {
            assertEqual(json.title, "MaaFramework Project Interface V2", "interface schema title");
            assertEqual(json.properties?.interface_version?.const, 2, "interface_version const");
        },
    },
    {
        path: "interface_import.schema.json",
        validate: (json) => assertRecord(json.properties?.task, "interface import task property"),
    },
    {
        path: "interface_config.schema.json",
        validate: (json) => assertRequired(json.required, "controller", "interface config"),
    },
    {
        path: "pipeline.schema.json",
        validate: (json) => assertRecord(json.$defs?.Node, "pipeline Node definition"),
    },
];

await main();

async function main() {
    await mkdir(targetDir, {recursive: true});
    const synced = [];
    for (const schema of upstreamSchemas) {
        synced.push(await fetchAndWrite(schema));
    }

    const manifest = {
        schemaVersion: 1,
        source: {
            repository: "MaaXYZ/MaaFramework",
            ref: upstreamRef,
        },
        files: synced,
    };
    await writeFile(join(targetDir, "schema-manifest.json"), prettyJson(manifest), "utf8");
    console.log(`Synced ${synced.length} schema files into ${targetDir}`);
}

async function fetchAndWrite(schema) {
    const {text, url} = await fetchSchemaText(schema.path);
    let json;
    try {
        json = JSON.parse(text);
    } catch (error) {
        throw new Error(`Fetched schema is not valid JSON: ${schema.path}. ${error.message}`);
    }

    schema.validate(json);
    const content = normalizeJsonText(text);
    await writeFile(join(targetDir, schema.path), content, "utf8");
    return {
        path: `${targetDir}/${schema.path}`,
        upstreamPath: `tools/${schema.path}`,
        url,
        sha256: sha256(content),
    };
}

async function fetchSchemaText(path) {
    const errors = [];
    for (const baseUrl of baseUrls) {
        const url = `${baseUrl}/${path}`;
        try {
            return {
                text: await fetchTextWithRetry(url),
                url,
            };
        } catch (error) {
            errors.push(`${url}: ${error.message}`);
        }
    }
    throw new Error(`Failed to fetch ${path} from all schema sources:\n${errors.join("\n")}`);
}

async function fetchTextWithRetry(url) {
    let lastError;
    const attempts = Number.isFinite(downloadAttempts) && downloadAttempts > 0 ? downloadAttempts : 1;
    for (let attempt = 1; attempt <= attempts; attempt += 1) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`${response.status} ${response.statusText}`);
            }
            return await response.text();
        } catch (error) {
            lastError = error;
            if (attempt === attempts) {
                break;
            }
            const waitMs = 500 * attempt;
            console.warn(`Fetch failed (${attempt}/${attempts}) for ${url}: ${error.message}. Retry in ${waitMs}ms.`);
            await delay(waitMs);
        }
    }
    throw new Error(`Failed to fetch ${url}: ${lastError.message}`);
}

function delay(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

function prettyJson(value) {
    return JSON.stringify(value, null, 4) + "\n";
}

function normalizeJsonText(text) {
    return text.replace(/^\uFEFF/u, "").trimEnd() + "\n";
}

function sha256(content) {
    return createHash("sha256").update(content).digest("hex");
}

function assertRecord(value, label) {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
        throw new Error(`${label} must be an object`);
    }
}

function assertEqual(actual, expected, label) {
    if (actual !== expected) {
        throw new Error(`${label} must be ${JSON.stringify(expected)}`);
    }
}

function assertRequired(required, field, label) {
    if (!Array.isArray(required) || !required.includes(field)) {
        throw new Error(`${label} must require ${field}`);
    }
}
