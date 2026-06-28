import { describe, expect, it } from "vitest";
import {
  cn,
  clampInput,
  formatDate,
  formatRelativeTime,
  getMatchBg,
  getMatchColor,
  INPUT_LIMITS,
  jobPreviewText,
  sanitizeUserInput,
  STATUS_CONFIG,
  stripHtml,
} from "@/lib/utils";

describe("cn", () => {
  it("merges class names and resolves Tailwind conflicts", () => {
    expect(cn("px-2", "px-4")).toBe("px-4");
    expect(cn("text-sm", false && "hidden", "font-medium")).toBe("text-sm font-medium");
  });
});

describe("formatDate", () => {
  it("formats ISO dates in en-US locale", () => {
    const formatted = formatDate("2026-01-15T10:00:00Z");
    expect(formatted).toMatch(/Jan/);
    expect(formatted).toMatch(/2026/);
  });
});

describe("formatRelativeTime", () => {
  it("returns Today for current timestamp", () => {
    expect(formatRelativeTime(new Date().toISOString())).toBe("Today");
  });

  it("returns Yesterday for one day ago", () => {
    const yesterday = new Date(Date.now() - 86400000).toISOString();
    expect(formatRelativeTime(yesterday)).toBe("Yesterday");
  });

  it("returns weeks ago for dates within a month", () => {
    const twoWeeksAgo = new Date(Date.now() - 14 * 86400000).toISOString();
    expect(formatRelativeTime(twoWeeksAgo)).toBe("2w ago");
  });
});

describe("match helpers", () => {
  it("returns high-match colors at 75%+", () => {
    expect(getMatchColor(80)).toContain("emerald");
    expect(getMatchBg(80)).toContain("emerald");
  });

  it("returns mid-match colors between 50–74%", () => {
    expect(getMatchColor(60)).toContain("amber");
    expect(getMatchBg(60)).toContain("amber");
  });

  it("returns low-match colors below 50%", () => {
    expect(getMatchColor(30)).toContain("rose");
    expect(getMatchBg(30)).toContain("rose");
  });
});

describe("guardrail input helpers", () => {
  it("clamps input to max length", () => {
    expect(clampInput("a".repeat(300), 200).length).toBeLessThanOrEqual(200);
  });

  it("sanitizes HTML before clamping", () => {
    const cleaned = sanitizeUserInput("<b>React</b> engineer", INPUT_LIMITS.companyRole);
    expect(cleaned).toBe("React engineer");
    expect(cleaned).not.toContain("<");
  });
});

describe("stripHtml", () => {
  it("removes HTML tags and entities from job descriptions", () => {
    const raw = '<p data-pm-slice="1 1 []"><strong>REQ ID: CSQ427R198</strong></p>';
    expect(stripHtml(raw)).toBe("REQ ID: CSQ427R198");
  });

  it("builds a clean preview snippet", () => {
    expect(
      jobPreviewText({
        description: "<p>Build ML pipelines for production systems.</p>",
      })
    ).toBe("Build ML pipelines for production systems.");
  });
});

describe("STATUS_CONFIG", () => {
  it("defines all application statuses", () => {
    expect(Object.keys(STATUS_CONFIG).sort()).toEqual(
      ["archived", "interview", "not_selected", "saved", "selected", "submitted"].sort()
    );
  });

  it("includes label and color tokens for each status", () => {
    for (const key of Object.keys(STATUS_CONFIG) as Array<keyof typeof STATUS_CONFIG>) {
      const cfg = STATUS_CONFIG[key];
      expect(cfg.label).toBeTruthy();
      expect(cfg.color).toContain("text-");
      expect(cfg.bg).toContain("bg-");
    }
  });
});
