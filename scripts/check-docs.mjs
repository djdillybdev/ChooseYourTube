#!/usr/bin/env node

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const excludedDirectories = new Set([
  ".git",
  ".portfolio-artifacts",
  ".venv",
  "node_modules",
]);
const documentationRoots = [
  "README.md",
  "CHANGELOG.md",
  "CONTRIBUTING.md",
  "SECURITY.md",
  "docs",
  "backend/README.md",
  "frontend/README.md",
];
const failures = [];

function markdownFiles(path) {
  const absolute = resolve(repositoryRoot, path);
  if (!existsSync(absolute)) return [];
  if (!statSync(absolute).isDirectory())
    return absolute.endsWith(".md") ? [absolute] : [];
  return readdirSync(absolute, { withFileTypes: true }).flatMap((entry) => {
    if (entry.isDirectory() && excludedDirectories.has(entry.name)) return [];
    return markdownFiles(relative(repositoryRoot, join(absolute, entry.name)));
  });
}

for (const file of documentationRoots.flatMap(markdownFiles)) {
  const content = readFileSync(file, "utf8");
  if (content.includes("<repository-url>")) {
    failures.push(
      `${relative(repositoryRoot, file)} contains <repository-url>`,
    );
  }

  for (const match of content.matchAll(/\[[^\]]*\]\(([^)]+)\)/g)) {
    let destination = match[1].trim();
    if (destination.startsWith("<") && destination.endsWith(">")) {
      destination = destination.slice(1, -1);
    }
    if (/^(?:https?:|mailto:|#)/.test(destination)) continue;
    const path = decodeURIComponent(destination.split("#", 1)[0]);
    if (!path) continue;
    const target = resolve(dirname(file), path);
    if (!existsSync(target)) {
      failures.push(
        `${relative(repositoryRoot, file)} links to missing ${destination}`,
      );
    }
  }
}

if (failures.length) {
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log("Documentation links and placeholders are valid.");
