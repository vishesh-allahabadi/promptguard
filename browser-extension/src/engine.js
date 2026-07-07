const SEVERITY_SCORE = { LOW: 0, MEDIUM: 1, HIGH: 2, CRITICAL: 3 };
const CATEGORY_PRIORITY = {
  aadhaar_like_id: 3,
  pan_like_id: 3,
  jwt_token: 3,
  bearer_token: 3,
  phone: 1
};

const DEFAULT_SETTINGS = {
  blockOn: ["CRITICAL", "HIGH"],
  warnOn: ["MEDIUM"],
  customerNames: [],
  clientNames: [],
  companyNames: [],
  confidentialTerms: [],
  allowSendAnyway: true
};

const RULES = [
  rule("anthropic_api_key", "Anthropic-style API key", /\bsk-ant-[A-Za-z0-9_-]{20,}\b/g, "CRITICAL", "[SECRET_REMOVED]", "AI provider key detected"),
  rule("openai_api_key", "OpenAI-style API key", /\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b/g, "CRITICAL", "[SECRET_REMOVED]", "AI provider key detected"),
  rule("github_token", "GitHub token", /\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b/g, "CRITICAL", "[SECRET_REMOVED]", "Source control token detected"),
  rule("stripe_key", "Stripe API key", /\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{16,}\b/g, "CRITICAL", "[SECRET_REMOVED]", "Payment provider key detected"),
  rule("aws_access_key_id", "AWS access key ID", /\b(?:AKIA|ASIA)[A-Z0-9]{16}\b/g, "CRITICAL", "[SECRET_REMOVED]", "Cloud access key detected"),
  rule("google_api_key", "Google API key", /\bAIza[0-9A-Za-z_-]{35}\b/g, "CRITICAL", "[SECRET_REMOVED]", "Cloud API key detected"),
  rule("slack_token", "Slack token", /\bxox(?:b|p|o|a|r|s)-[0-9A-Za-z-]{20,}\b/g, "CRITICAL", "[SECRET_REMOVED]", "Workspace token detected"),
  rule("resend_api_key", "Resend API key", /\bre_[A-Za-z0-9_-]{20,}\b/g, "CRITICAL", "[SECRET_REMOVED]", "Email provider key detected"),
  rule("twilio_account_sid", "Twilio account SID", /\bAC[a-fA-F0-9]{32}\b/g, "CRITICAL", "[SECRET_REMOVED]", "Messaging account ID detected"),
  rule("twilio_auth_token_like", "Twilio auth token-like value", /\btwilio[_-]?auth[_-]?token\b\s*[:=]\s*['"]?[a-f0-9]{32}\b/gi, "CRITICAL", "[SECRET_REMOVED]", "Messaging auth token detected"),
  rule("vercel_token", "Vercel token", /\bvercel_[A-Za-z0-9_-]{20,}\b/g, "CRITICAL", "[SECRET_REMOVED]", "Deployment token detected"),
  rule("cloudflare_api_token", "Cloudflare API token", /\bcloudflare[_-]?(?:api[_-]?)?token\b\s*[:=]\s*['"]?[A-Za-z0-9_-]{20,}\b/gi, "CRITICAL", "[SECRET_REMOVED]", "Infrastructure token detected"),
  rule("jwt_token", "JWT token", /\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b/g, "CRITICAL", "[SECRET_REMOVED]", "JWT token detected"),
  rule("private_key_block", "Private key block", /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g, "CRITICAL", "[SECRET_REMOVED]", "Private key block detected"),
  rule("database_url", "Database connection URL", /\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis):\/\/[^\s'"<>]+/g, "CRITICAL", "[DATABASE_URL_REMOVED]", "Database connection URL detected"),
  rule("bearer_token", "Bearer token", /\bBearer\s+[A-Za-z0-9._~+/=-]{16,}/gi, "CRITICAL", "Bearer [SECRET_REMOVED]", "Bearer token detected"),
  rule("url_with_credentials", "URL with credentials", /\b[a-z][a-z0-9+.-]*:\/\/[^/\s:@]+:[^@\s/]+@[^\s]+/gi, "CRITICAL", "[URL_WITH_CREDENTIALS_REMOVED]", "URL credentials detected"),
  rule("password_assignment", "Password-like assignment", /\b(?:password|passwd|pwd|secret|api[_-]?key|token)\b\s*[:=]\s*['"]?[^'"\s]{6,}/gi, "CRITICAL", "[SECRET_REMOVED]", "Secret assignment detected"),
  rule("email", "Email address", /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, "HIGH", "[EMAIL]", "Email address detected"),
  rule("phone", "Phone number", /(?<!\w)(?:\+?\d{1,3}[-.\s]?)?(?:\d{5}[-.\s]?\d{5}|\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4})(?!\w)/g, "HIGH", "[PHONE]", "Phone number detected"),
  rule("ip_address", "IP address", /\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b/g, "HIGH", "[IP_ADDRESS]", "IP address detected"),
  rule("pan_like_id", "PAN-like ID", /\b[A-Z]{5}[0-9]{4}[A-Z]\b/g, "HIGH", "[PAN_LIKE_ID]", "Government ID-like value detected"),
  rule("aadhaar_like_id", "Aadhaar-like ID", /(?<!\d)\d{4}(?:[\s-]?\d{4}){2,3}(?![\s-]?\d)/g, "HIGH", "[AADHAAR_LIKE_ID]", "Government ID-like value detected"),
  rule("production_indicator", "Production environment indicator", /\b(?:prod|production|live environment|live key|live database|customer database)\b/gi, "MEDIUM", "", "Production context detected"),
  rule("financial_context", "Financial context keyword", /\b(?:invoice|revenue|salary|payroll|bank account|valuation|profit|loss|margin|refund|chargeback|payment|financial)\b/gi, "MEDIUM", "", "Financial context detected"),
  rule("legal_context", "Legal context keyword", /\b(?:contract|lawsuit|legal notice|nda|settlement|compliance|breach|attorney|lawyer)\b/gi, "MEDIUM", "", "Legal context detected"),
  rule("health_context", "Health context keyword", /\b(?:diagnosis|patient|medical|health|prescription|clinic|treatment|symptom|blood report)\b/gi, "MEDIUM", "", "Health context detected"),
  rule("confidential_business_keyword", "Confidential business keyword", /\b(?:confidential|internal only|trade secret|board deck|pricing model|private roadmap|acquisition target)\b/gi, "MEDIUM", "", "Confidential business context detected"),
  rule("financial_amount", "Financial amount", /(?<!\w)(?:₹\s?\d[\d,]*(?:\.\d+)?|\$\s?\d[\d,]*(?:\.\d+)?|USD\s?\d[\d,]*(?:\.\d+)?|INR\s?\d[\d,]*(?:\.\d+)?)(?!\w)/g, "MEDIUM", "[AMOUNT]", "Financial amount detected"),
  rule("date", "Exact date", /\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b/gi, "MEDIUM", "[DATE]", "Exact date detected")
];

export function scanText(text, settings = {}) {
  const effectiveSettings = normalizeSettings(settings);
  const findings = dedupeOverlaps([...scanRules(text), ...scanConfigured(text, effectiveSettings)]);
  const riskLevel = riskForFindings(findings);
  return {
    riskLevel,
    policy: policyForRisk(riskLevel, effectiveSettings),
    categories: [...new Set(findings.map((finding) => finding.category))].sort(),
    findings
  };
}

export function anonymizeText(text, settings = {}) {
  const scan = scanText(text, settings);
  const labels = new Map();
  let safeText = text;
  for (const finding of [...scan.findings].sort((a, b) => b.start - a.start)) {
    const original = text.slice(finding.start, finding.end);
    const replacement = replacementFor(original, finding, labels);
    safeText = safeText.slice(0, finding.start) + replacement + safeText.slice(finding.end);
  }
  safeText = rewriteSensitivePhrases(safeText);
  return { ...scan, safeText };
}

export function riskForFindings(findings) {
  if (!findings.length) return "LOW";
  return findings.reduce((highest, finding) => {
    return SEVERITY_SCORE[finding.severity] > SEVERITY_SCORE[highest] ? finding.severity : highest;
  }, "LOW");
}

export function policyForRisk(risk, settings = {}) {
  const effectiveSettings = normalizeSettings(settings);
  if (effectiveSettings.blockOn.includes(risk)) return "block";
  if (effectiveSettings.warnOn.includes(risk)) return "warn";
  return "allow";
}

export function maskPreview(value) {
  const compact = String(value).replace(/\s+/g, " ").trim();
  if (!compact) return "";
  if (compact.includes("@")) {
    const [name, domain = ""] = compact.split("@");
    return `${name.slice(0, 4)}@…${domain.slice(-3)}`;
  }
  if (compact.length <= 10) return `${compact.slice(0, 2)}…${compact.slice(-2)}`;
  return `${compact.slice(0, 8)}…${compact.slice(-4)}`;
}

function rule(category, label, regex, severity, replacement, message) {
  return { category, label, regex, severity, replacement, message };
}

function normalizeSettings(settings) {
  return { ...DEFAULT_SETTINGS, ...settings };
}

function scanRules(text) {
  const findings = [];
  for (const ruleConfig of RULES) {
    const regex = cloneRegex(ruleConfig.regex);
    for (const match of text.matchAll(regex)) {
      const value = match[0];
      findings.push(findingFromRule(ruleConfig, match.index ?? 0, value));
    }
  }
  return findings;
}

function scanConfigured(text, settings) {
  const configured = [
    ["customer_name", "Configured customer name", settings.customerNames, "HIGH", "Person", "Configured customer name detected"],
    ["client_name", "Configured client name", settings.clientNames, "HIGH", "Client", "Configured client name detected"],
    ["company_name", "Configured company name", settings.companyNames, "MEDIUM", "Company", "Configured company name detected"],
    ["configured_confidential_term", "Configured confidential term", settings.confidentialTerms, "HIGH", "Confidential Term", "Configured confidential term detected"]
  ];
  const findings = [];
  for (const [category, label, values, severity, prefix, message] of configured) {
    for (const value of values || []) {
      const clean = String(value).trim();
      if (!clean) continue;
      const regex = new RegExp(`\\b${escapeRegExp(clean)}\\b`, "gi");
      for (const match of text.matchAll(regex)) {
        findings.push({
          category,
          label,
          severity,
          start: match.index ?? 0,
          end: (match.index ?? 0) + match[0].length,
          replacement: `[${prefix.toUpperCase().replace(/\s+/g, "_")}]`,
          preview: maskPreview(match[0]),
          message
        });
      }
    }
  }
  return findings;
}

function findingFromRule(ruleConfig, start, value) {
  return {
    category: ruleConfig.category,
    label: ruleConfig.label,
    severity: ruleConfig.severity,
    start,
    end: start + value.length,
    replacement: ruleConfig.replacement,
    preview: maskPreview(value),
    message: ruleConfig.message
  };
}

function dedupeOverlaps(findings) {
  const kept = [];
  for (const finding of [...findings].sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start))) {
    const overlaps = kept.filter((existing) => !(finding.end <= existing.start || finding.start >= existing.end));
    if (!overlaps.length) {
      kept.push(finding);
      continue;
    }
    const strongest = [...overlaps, finding].sort(compareFindingStrength)[0];
    if (strongest === finding) {
      for (const overlap of overlaps) {
        kept.splice(kept.indexOf(overlap), 1);
      }
      kept.push(finding);
    }
  }
  return kept.sort((a, b) => a.start - b.start);
}

function compareFindingStrength(a, b) {
  const severity = SEVERITY_SCORE[b.severity] - SEVERITY_SCORE[a.severity];
  if (severity !== 0) return severity;
  const categoryPriority = (CATEGORY_PRIORITY[b.category] || 0) - (CATEGORY_PRIORITY[a.category] || 0);
  if (categoryPriority !== 0) return categoryPriority;
  return (b.end - b.start) - (a.end - a.start);
}

function replacementFor(original, finding, labels) {
  if (finding.category === "financial_amount") return generalizeMoney(original);
  if (finding.category === "date") return generalizeDate(original);
  if (finding.category === "customer_name") return stableLabel(original, labels, "Person");
  if (finding.category === "client_name") return stableLabel(original, labels, "Client");
  if (finding.category === "company_name") return stableLabel(original, labels, "Company");
  if (finding.category === "configured_confidential_term") return stableLabel(original, labels, "Confidential Term");
  return finding.replacement || original;
}

function stableLabel(original, labels, prefix) {
  const key = `${prefix}:${original.toLowerCase()}`;
  if (!labels.has(key)) {
    const count = [...labels.values()].filter((value) => value.startsWith(prefix)).length;
    labels.set(key, `${prefix} ${String.fromCharCode(65 + count)}`);
  }
  return labels.get(key);
}

function generalizeMoney(value) {
  const compact = value.replace(/[, ]/g, "");
  const currency = value.includes("₹") || compact.toUpperCase().startsWith("INR") ? "₹" : "$";
  const match = compact.match(/\d+(?:\.\d+)?/);
  if (!match) return "[AMOUNT]";
  const amount = Number(match[0]);
  if (!Number.isFinite(amount)) return "[AMOUNT]";
  if (currency === "₹" && amount >= 100000) return `around ₹${(amount / 100000).toFixed(1)} lakh`;
  if (amount >= 1000) {
    const thousands = amount / 1000;
    return `around ${currency}${thousands >= 10 ? thousands.toFixed(0) : thousands.toFixed(1)}k`;
  }
  return `around ${currency}${amount.toFixed(0)}`;
}

function generalizeDate(value) {
  const iso = value.match(/^(\d{4})-(\d{2})-\d{2}$/);
  if (iso) {
    const date = new Date(`${value}T00:00:00Z`);
    if (!Number.isNaN(date.getTime())) {
      return `around ${date.toLocaleString("en", { month: "long", timeZone: "UTC" })} ${iso[1]}`;
    }
  }
  return "[DATE]";
}

function rewriteSensitivePhrases(text) {
  return text
    .replace(/\bStripe\s+live\s+key\b/gi, "payment provider live key")
    .replace(/\bOpenAI\s+(?:api\s+)?key\b/gi, "AI provider key")
    .replace(/\bAnthropic\s+(?:api\s+)?key\b/gi, "AI provider key");
}

function cloneRegex(regex) {
  return new RegExp(regex.source, regex.flags);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
