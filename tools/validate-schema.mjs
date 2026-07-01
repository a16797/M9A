import {existsSync, readFileSync} from "node:fs";

const SCHEMA_DIR = "deps/tools";
const EXPECTED_SCHEMA_FILES = [
    "custom.action.schema.json",
    "custom.recognition.schema.json",
    "interface.schema.json",
    "interface_config.schema.json",
    "interface_import.schema.json",
    "pipeline.schema.json",
];
const CONTROLLER_TYPES = [
    "Adb",
    "Win32",
    "MacOS",
    "PlayCover",
    "Gamepad",
    "WlRoots",
];

assertMissing("maa-project.json");
assertMissing("maa-project.lock.json");
assertMissing("maa-project..lock.json");
assertMissing("assets/interface.json");
assertMissing("assets/resource");

if (!existsSync(SCHEMA_DIR)) {
    throw new Error("Missing " + SCHEMA_DIR + " directory");
}

for (const fileName of EXPECTED_SCHEMA_FILES) {
    assertRecord(readJson(SCHEMA_DIR + "/" + fileName), SCHEMA_DIR + "/" + fileName);
}

const interfaceJson = readJson("interface.json");
const interfaceSchema = readJson(SCHEMA_DIR + "/interface.schema.json");
const packageJson = readJson("package.json");
const workspaceYaml = readText("pnpm-workspace.yaml");

assertRecord(interfaceJson, "interface.json");
assertEqual(interfaceJson.interface_version, 2, "interface.json interface_version must be 2");
assertNonEmptyString(interfaceJson.name, "interface.json name");
assertNonEmptyString(interfaceJson.version, "interface.json version");
assertArrayOfRecords(interfaceJson.controller, "interface.json controller");
assertArrayOfRecords(interfaceJson.resource, "interface.json resource");
assertArrayOfRecords(interfaceJson.group, "interface.json group");
assertArrayOfRecords(interfaceJson.task, "interface.json task");
assertRecord(interfaceJson.option, "interface.json option");
assertArrayOfStrings(interfaceJson.import, "interface.json import");

for (const [
    index,
    controller,
] of interfaceJson.controller.entries()) {
    assertNonEmptyString(controller.name, "interface.json controller[" + index + "].name");
    assertEnum(controller.type, CONTROLLER_TYPES, "interface.json controller[" + index + "].type");
    if (controller.label !== undefined) {
        assertNonEmptyString(controller.label, "interface.json controller[" + index + "].label");
    }
}

const controllerNames = new Set(interfaceJson.controller.map((controller) => controller.name));
for (const [
    index,
    resource,
] of interfaceJson.resource.entries()) {
    assertNonEmptyString(resource.name, "interface.json resource[" + index + "].name");
    assertArrayOfStrings(resource.path, "interface.json resource[" + index + "].path");
    for (const [
        pathIndex,
        path,
    ] of resource.path.entries()) {
        assertRootRelativePath(path, "interface.json resource[" + index + "].path[" + pathIndex + "]");
        if (!path.startsWith("./resource/")) {
            throw new Error(
                "interface.json resource[" + index + "].path[" + pathIndex + "] must start with ./resource/",
            );
        }
    }
    if (resource.controller !== undefined) {
        assertArrayOfStrings(resource.controller, "interface.json resource[" + index + "].controller");
        for (const controllerName of resource.controller) {
            if (!controllerNames.has(controllerName)) {
                throw new Error(
                    "interface.json resource[" +
                        index +
                        "].controller references unknown controller: " +
                        controllerName,
                );
            }
        }
    }
}

for (const [
    index,
    group,
] of interfaceJson.group.entries()) {
    assertNonEmptyString(group.name, "interface.json group[" + index + "].name");
}

if (interfaceJson.agent !== undefined) {
    assertArrayOfRecords(interfaceJson.agent, "interface.json agent");
    for (const [
        index,
        agent,
    ] of interfaceJson.agent.entries()) {
        assertNonEmptyString(agent.child_exec, "interface.json agent[" + index + "].child_exec");
        if (agent.child_args !== undefined) {
            assertArrayOfStrings(agent.child_args, "interface.json agent[" + index + "].child_args");
        }
        if (agent.identifier !== undefined) {
            assertNonEmptyString(agent.identifier, "interface.json agent[" + index + "].identifier");
        }
    }
}

for (const [
    index,
    importPath,
] of interfaceJson.import.entries()) {
    assertRootRelativePath(importPath, "interface.json import[" + index + "]");
    if (!importPath.startsWith("./tasks/")) {
        throw new Error("interface.json import[" + index + "] must start with ./tasks/");
    }
}

assertRecord(interfaceSchema, SCHEMA_DIR + "/interface.schema.json");
assertEqual(
    interfaceSchema.title,
    "MaaFramework Project Interface V2",
    SCHEMA_DIR + "/interface.schema.json title must be MaaFramework Project Interface V2",
);
assertRecord(interfaceSchema.properties, SCHEMA_DIR + "/interface.schema.json properties");
assertRecord(
    interfaceSchema.properties.interface_version,
    SCHEMA_DIR + "/interface.schema.json properties.interface_version",
);
assertEqual(
    interfaceSchema.properties.interface_version.const,
    2,
    SCHEMA_DIR + "/interface.schema.json interface_version const must be 2",
);

assertRecord(packageJson, "package.json");
assertSlug(packageJson.name, "package.json name");
assertVersion(packageJson.version, "package.json version");
assertNonEmptyString(packageJson.license, "package.json license");
assertEqual(packageJson.private, true, "package.json private must be true");
assertEqual(packageJson.type, "module", "package.json type must be module");
assertNonEmptyString(packageJson.packageManager, "package.json packageManager");
if (!packageJson.packageManager.startsWith("pnpm@")) {
    throw new Error("package.json packageManager must use pnpm");
}
assertRecord(packageJson.engines, "package.json engines");
assertNonEmptyString(packageJson.engines.node, "package.json engines.node");
assertRecord(packageJson.scripts, "package.json scripts");
for (const script of [
    "check",
    "check:maa",
    "check:py",
    "check:schema",
    "install:py",
]) {
    assertNonEmptyString(packageJson.scripts[script], "package.json scripts." + script);
}
assertRecord(packageJson.devDependencies, "package.json devDependencies");
assertNonEmptyString(
    packageJson.devDependencies["@nekosu/maa-tools"],
    "package.json devDependencies.@nekosu/maa-tools",
);

if (!/^packages:\s*\[\]\s*$/u.test(workspaceYaml.trim())) {
    throw new Error("pnpm-workspace.yaml must keep an explicit empty packages array");
}

console.log("[OK] M9A schema shape is valid");

function readJson(path) {
    return JSON.parse(readText(path));
}

function readText(path) {
    if (!existsSync(path)) {
        throw new Error(path + " is missing");
    }
    return readFileSync(path, "utf8");
}

function assertRecord(value, label) {
    if (typeof value !== "object" || value === null || Array.isArray(value)) {
        throw new Error(label + " must be an object");
    }
}

function assertArrayOfRecords(value, label) {
    if (
        !Array.isArray(value) ||
        value.some((item) => typeof item !== "object" || item === null || Array.isArray(item))
    ) {
        throw new Error(label + " must be an array of objects");
    }
}

function assertArrayOfStrings(value, label) {
    if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
        throw new Error(label + " must be an array of strings");
    }
}

function assertNonEmptyString(value, label) {
    if (typeof value !== "string" || value.trim() === "") {
        throw new Error(label + " must be a non-empty string");
    }
}

function assertSlug(value, label) {
    assertNonEmptyString(value, label);
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/u.test(value)) {
        throw new Error(label + " must be an ASCII kebab-case slug");
    }
}

function assertVersion(value, label) {
    assertNonEmptyString(value, label);
    if (!/^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$/u.test(value)) {
        throw new Error(label + " must be a SemVer version");
    }
}

function assertEnum(value, allowed, label) {
    if (!allowed.includes(value)) {
        throw new Error(label + " must be one of: " + allowed.join(", "));
    }
}

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(message);
    }
}

function assertMissing(path) {
    if (existsSync(path)) {
        throw new Error(path + " should not exist in the migrated root layout");
    }
}

function assertRootRelativePath(value, label) {
    assertNonEmptyString(value, label);
    if (!value.startsWith("./") || value.includes("..") || value.includes("\\")) {
        throw new Error(label + " must be a ./ relative path without .. or backslashes");
    }
}
