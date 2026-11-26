import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { Dropdown } from "./Dropdown";

const OPTIONS = [
  { name: "Sako", count: 4 },
  { name: "Bawar", count: 3 },
];

const draw = (value?: string) =>
  renderToStaticMarkup(
    <Dropdown label="Filter by owner" all="All owners" empty="No owners" options={OPTIONS} value={value} onChange={() => {}} />,
  );

describe("Dropdown clear button", () => {
  it("shows an × to clear the filter when a value is picked", () => {
    const html = draw("Sako");
    expect(html).toContain('class="dagwick-dd-clear"');
    expect(html).toContain('aria-label="Clear: All owners"');
    expect(html).toContain('type="button"');
  });

  it("has no × when nothing is picked", () => {
    expect(draw()).not.toContain("dagwick-dd-clear");
  });

  it("keeps the × outside the dropdown button (no button inside a button)", () => {
    const html = draw("Sako");
    const select = html.indexOf('class="dagwick-select is-set"');
    const selectEnd = html.indexOf("</button>", select);
    expect(html.indexOf("dagwick-dd-clear")).toBeGreaterThan(selectEnd);
  });
});
