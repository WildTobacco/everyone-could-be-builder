---
name: dashboard-builder
description: Create a ready-to-use BIDV dashboard from the bundled fixed HTML template. Use when asked to build a dashboard, KPI dashboard, reporting dashboard, analytics dashboard, or visualization dashboard from a dashboard name and output path, especially prompts shaped like `[activate skill] [dashboard name] [file path]`. Use the template's preset five tabs, four overview cards, numbered Item slots, paper-folder button toggles, and chart slots without redesigning them.
---

# Dashboard Builder

Use [assets/dashboard-template.html](assets/dashboard-template.html) as the output itself. Copy it to the requested destination, replace `{{DASHBOARD_NAME}}` with the requested dashboard name, then populate only the requested items.

## Invocation

Interpret `[activate skill] [dashboard name] [file path]` as:

- Use the second bracketed value for `{{DASHBOARD_NAME}}`.
- If the third value ends in `.html`, save to that exact file.
- Otherwise create the destination directory and save as `index.html` inside it.

## Populate items

- Keep the template's HTML, CSS, BIDV header, five primary tabs, numbered items, and JavaScript tab behavior intact.
- Let the user target a slot with a short prompt such as `put a line chart in Item 12`. Locate it with `data-item="item-12"` or `window.getDashboardItem(12)`. The original descriptive `data-object` names remain available through `window.getDashboardObject(name)`.
- Numbering is global and unique: overview cards are Items 1–4, overview charts are Items 5–7, and detail charts are Items 8–55 in Tab → Button → Chart order.
- When populating an item, remove only that item's `.item-label`; preserve labels in unspecified items and never fabricate values or visualization content.
- When placement is unspecified, fill the next blank slot in document order.
- When a visualization is described generally, copy the closest matching native SVG rendering pattern from the template's existing CSS conventions. Preserve the exact card, title, legend, axis, tooltip, color, font, size, and spacing styles.
- Use `window.dashboardChartDefaults` and the bundled CSS chart classes for unspecified series colors. Match the original demo exactly: default to teal `#0d5d56`, then yellow `#ffc72c`, then grey `#a8a6a0`.
- Give every bar and column rounded corners with `class="chart-column"` plus explicit SVG `rx="6" ry="6"`. For a stacked column, clip all segments to one rounded outer rectangle so the stack has rounded outer corners and flat internal joins.
- For a prompt asking for a stacked column that presents revenue/performance target met, achievement versus target, or `KH`, use the template's built-in `window.renderTargetMetChart` renderer. Do not invent a different chart design. It reproduces the demo's teal actual segment, light-grey remaining-to-KH segment, translucent-teal over-KH segment, KH and actual labels, five horizontal scale lines, wrapped category labels, centered legend, and rounded outer column corners.
- Place every KH label mandatorily to the right of its column at the target-height boundary with `text-anchor="start"`. Never center a KH label above a column, because it can overlap the actual-value label when the two values are close. Apply this rule to below-target, exactly-on-target, and above-target columns.
- Pass any number of categories in `items`; do not assume exactly five. Each category must have `label`, `actual`, and `target` values. Example for Item 6:

```html
<script>
renderTargetMetChart(6, {
  title: "Các chỉ tiêu KHKD khác",
  actualLabel: "KQKD",
  targetLabel: "KH",
  unit: "tỷ đồng",
  items: [
    { label: "1", actual: 3465, target: 6100 },
    { label: "2", actual: 2532, target: 5000 },
    { label: "3", actual: 5200, target: 6000 },
    { label: "4", actual: 1800, target: 2500 },
    { label: "5", actual: 900, target: 1500 }
  ]
});
</script>
```

- Insert the call after the bundled template script or invoke it from later application code so `window.getDashboardItem` is available. Use the user's real labels and numbers; never substitute the example values unless the user explicitly requests mock data.
- Add a chart header inside its assigned chart object only when populating that object.
- Keep data separate from rendering functions and label mock data explicitly.
- Never add tabs, cards, button panels, sidebars, or chart rows unless the user explicitly asks to change the template.
- Preserve the template's uniform 12px horizontal and vertical visualization gaps.
- Never place more than two charts in one row or more than four KPI cards in the score-card row.

## Verify

Open the generated HTML and confirm:

1. `Tổng quan`, `Tab 1`, `Tab 2`, `Tab 3`, and `Tab 4` switch correctly.
2. Every general tab has four working paper-folder buttons: `Button 1` through `Button 4`.
3. Tổng quan has four cards, two side-by-side chart slots, and one full-width chart slot.
4. Every folder panel has two side-by-side chart slots and one full-width chart slot.
5. The page stacks to one chart per row below the existing responsive breakpoint.
6. Every target/KH chart places each KH label to the right of its column without overlapping its actual-value label.

Return the generated HTML path and list the items populated.
