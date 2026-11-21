#!/usr/bin/env node

import { readFileSync, statSync } from "node:fs";
import { dirname, isAbsolute, resolve } from "node:path";

const errors = [];
const reportPath = process.argv[2];
if (!reportPath || process.argv.length !== 3) {
  process.stderr.write("Usage: validate-deployed-evidence.mjs <report.json>\n");
  process.exit(2);
}

let report;
try {
  report = JSON.parse(readFileSync(reportPath, "utf8"));
} catch {
  process.stderr.write("Invalid deployed evidence report JSON.\n");
  process.exit(2);
}

const nonEmpty = (value) => typeof value === "string" && value.trim().length > 0;
const validTime = (value) => nonEmpty(value) && Number.isFinite(Date.parse(value));
const reportDir = dirname(resolve(reportPath));
const evidenceExists = (path) => {
  if (!nonEmpty(path)) return false;
  try {
    return statSync(isAbsolute(path) ? path : resolve(reportDir, path)).isFile();
  } catch {
    return false;
  }
};

if (report.mode !== "deployed") errors.push("mode must be deployed");
if (!nonEmpty(report.runId)) errors.push("QA runId is required");
if (!nonEmpty(report.implementationRunId)) errors.push("implementationRunId is required");
if (!nonEmpty(report.target?.environment)) errors.push("target environment is required");
if (!nonEmpty(report.evidenceRevision)) errors.push("evidenceRevision is required");
const expectedArtifact = report.target?.expectedArtifact;
const observedArtifact = report.observedArtifact?.identity;
const observedAt = report.observedArtifact?.observedAt;
if (!nonEmpty(expectedArtifact) || !nonEmpty(observedArtifact)) {
  errors.push("expected and observed artifact identities are required");
} else if (expectedArtifact !== observedArtifact) {
  errors.push(`artifact identity mismatch: expected ${expectedArtifact}, observed ${observedArtifact}`);
}
if (!validTime(report.observedArtifact?.observedAt) || !nonEmpty(report.observedArtifact?.source)) {
  errors.push("observed artifact needs a timestamp and read-only observation source");
}

if (!Array.isArray(report.scenarios) || report.scenarios.length === 0 || !report.scenarios.some((scenario) => scenario?.required === true)) {
  errors.push("at least one deployed scenario is required");
} else {
  const scenarioIds = report.scenarios.map((scenario) => scenario?.id).filter(nonEmpty);
  if (scenarioIds.length !== report.scenarios.length) errors.push("every scenario needs a stable id");
  if (new Set(scenarioIds).size !== scenarioIds.length) errors.push("scenario ids must be unique");
  for (const scenario of report.scenarios) {
    const label = nonEmpty(scenario?.id) ? scenario.id : "unnamed scenario";
    if (!scenario?.required) continue;
    if (!["web", "api", "cli", "job"].includes(scenario.surface)) errors.push(`${label}: unsupported surface`);
    if (!nonEmpty(scenario.featureCoverage)) errors.push(`${label}: concrete feature coverage is required`);
    if (!nonEmpty(scenario.expected) || !nonEmpty(scenario.actual)) errors.push(`${label}: expected and actual results are required`);
    if (!validTime(scenario.capturedAt)) errors.push(`${label}: capture timestamp is required`);
    else if (validTime(observedAt) && Date.parse(scenario.capturedAt) < Date.parse(observedAt)) errors.push(`${label}: scenario capture predates artifact observation`);
    if (scenario.result !== "PASS") errors.push(`${label}: required scenario did not pass`);
    if (!Array.isArray(scenario.evidence) || scenario.evidence.length === 0) {
      errors.push(`${label}: required evidence is missing`);
      continue;
    }
    if (scenario.evidence.some((item) => item?.accepted !== true)) errors.push(`${label}: missing or rejected evidence blocks PASS`);
    if (scenario.evidence.some((item) => typeof item?.authOnly !== "boolean")) errors.push(`${label}: every evidence item must classify authOnly`);
    if (scenario.evidence.some((item) => !validTime(item?.capturedAt))) errors.push(`${label}: every evidence item needs a capture timestamp`);
    if (validTime(observedAt) && scenario.evidence.some((item) => validTime(item?.capturedAt) && Date.parse(item.capturedAt) < Date.parse(observedAt))) errors.push(`${label}: evidence capture predates artifact observation`);
    if (scenario.evidence.some((item) => !nonEmpty(item?.path))) errors.push(`${label}: every evidence item needs a path`);
    const accepted = scenario.evidence.filter((item) => item?.accepted === true && evidenceExists(item.path));
    if (accepted.length === 0) errors.push(`${label}: no accepted evidence`);
    if (scenario.evidence.some((item) => nonEmpty(item?.path) && !evidenceExists(item.path))) errors.push(`${label}: referenced evidence file does not exist`);
    if (scenario.surface === "web" && !accepted.some((item) => item.kind === "screenshot" && item.visuallyInspected === true)) {
      errors.push(`${label}: web evidence needs an accepted, visually inspected screenshot`);
    }
    if (accepted.length > 0 && accepted.every((item) => item.authOnly === true)) {
      errors.push(`${label}: auth-only evidence cannot prove feature coverage`);
    }
  }
}

const review = report.evidenceReview;
if (!review || review.independent !== true || review.status !== "ACCEPTED" || !nonEmpty(review.reviewer) || !nonEmpty(review.reviewerRunId)) {
  errors.push("fresh independent evidence review is required");
} else {
  if (review.reviewerRunId === report.runId || review.reviewerRunId === report.implementationRunId) errors.push("evidence reviewer run must differ from QA and implementation runs");
  if (review.reviewedRunId !== report.runId || review.reviewedImplementationRunId !== report.implementationRunId) errors.push("evidence review covers different run identities");
  if (review.reviewedArtifact !== observedArtifact) errors.push("evidence review covers a different artifact");
  if (review.reviewedEvidenceRevision !== report.evidenceRevision) errors.push("evidence review covers a different evidence revision");
  const evidenceTimes = (report.scenarios ?? []).flatMap((scenario) => [scenario?.capturedAt, ...(scenario?.evidence ?? []).map((item) => item?.capturedAt)]).filter(validTime).map(Date.parse);
  const freshnessFloor = Math.max(Date.parse(report.observedArtifact?.observedAt ?? 0) || 0, ...evidenceTimes);
  if (!validTime(review.reviewedAt) || Date.parse(review.reviewedAt) < freshnessFloor) {
    errors.push("evidence review is missing or stale");
  }
}

if (report.verdict !== "PASS") errors.push("report verdict must be PASS");

if (errors.length > 0) {
  process.stderr.write(`${errors.map((error) => `- ${error}`).join("\n")}\n`);
  process.exit(1);
}

process.stdout.write("Deployed evidence accepted.\n");
