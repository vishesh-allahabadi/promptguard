import assert from "node:assert/strict";
import { anonymizeText, scanText } from "../src/engine.js";

function test(name, fn) {
  try {
    fn();
    console.log(`ok - ${name}`);
  } catch (error) {
    console.error(`not ok - ${name}`);
    throw error;
  }
}

test("critical Stripe key and email are anonymised", () => {
  const input = "Production Stripe live key sk_live_FAKEstripeKey1234567890 failed for jane@example.com on invoice $12,430";
  const result = anonymizeText(input);
  assert.equal(result.riskLevel, "CRITICAL");
  assert.equal(result.policy, "block");
  assert.ok(result.categories.includes("stripe_key"));
  assert.ok(result.categories.includes("email"));
  assert.ok(result.categories.includes("financial_amount"));
  assert.ok(result.safeText.includes("[SECRET_REMOVED]"));
  assert.ok(result.safeText.includes("[EMAIL]"));
  assert.ok(result.safeText.includes("around $12k"));
  assert.ok(!result.safeText.includes("sk_live_FAKEstripeKey1234567890"));
  assert.ok(!result.safeText.includes("jane@example.com"));
});

test("harmless prompt is low risk", () => {
  const result = scanText("How do I refactor this harmless Python function?");
  assert.equal(result.riskLevel, "LOW");
  assert.equal(result.policy, "allow");
  assert.deepEqual(result.findings, []);
});

test("configured confidential terms and clients use stable labels", () => {
  const result = anonymizeText("Project Sundial failed for Acme Retail", {
    confidentialTerms: ["Project Sundial"],
    clientNames: ["Acme Retail"]
  });
  assert.equal(result.riskLevel, "HIGH");
  assert.equal(result.policy, "block");
  assert.ok(result.safeText.includes("Confidential Term A"));
  assert.ok(result.safeText.includes("Client A"));
  assert.ok(!result.safeText.includes("Project Sundial"));
  assert.ok(!result.safeText.includes("Acme Retail"));
});

test("JWT detection removes token", () => {
  const input = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiYWRtaW4iOnRydWV9.FAKEsignatureValue1234567890abcdef";
  const result = anonymizeText(input);
  assert.equal(result.riskLevel, "CRITICAL");
  assert.ok(result.safeText.includes("[SECRET_REMOVED]"));
  assert.ok(!result.safeText.includes("eyJhbGciOiJIUzI1Ni"));
});

test("Aadhaar-like grouped ID is fully redacted", () => {
  const result = anonymizeText("ID 1234 5678 9012 is in the prompt");
  assert.equal(result.riskLevel, "HIGH");
  assert.ok(result.safeText.includes("[AADHAAR_LIKE_ID]"));
  assert.ok(!result.safeText.includes("1234 5678 9012"));
});

test("overlap dedupe avoids leaking bearer token", () => {
  const input = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.FAKEsignatureValue1234567890abcdef";
  const result = anonymizeText(input);
  assert.equal(result.riskLevel, "CRITICAL");
  assert.ok(result.findings.length <= 2);
  assert.ok(!result.safeText.includes("eyJhbGciOiJIUzI1Ni"));
});
