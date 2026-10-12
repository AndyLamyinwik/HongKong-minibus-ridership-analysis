# Website design system

The website presents the existing Hong Kong minibus study as an editorial research publication. Its visual emphasis is the difference between Green and Red Minibus passenger journeys, supported by the same evidence and definitions used in the Python, SQL and Streamlit project. Phase 6B extends the approved homepage through four analytical chapters while retaining its hero, finding strip and annual trend chart. This document describes the design and interaction specification; implementation checks and screenshots belong in the [validation record](validation.md).

## Visual identity

Use a warm paper background, dark typography and restrained transport colors. Typography, measured spacing and chart lines supply the visual character. Avoid stock imagery, decorative motion, repeated card grids and gradients. The four findings form a flat strip divided by fine rules rather than four independent containers.

| Token | Hex | Purpose |
| --- | --- | --- |
| Paper | `#f6f4ed` | Main page and chart background |
| Ink | `#172b32` | Headings, body text and focus outlines |
| Muted | `#53645f` | Supporting text, axis labels and secondary navigation |
| Jade | `#236451` | Green Minibus series, related figures and selected controls |
| Coral | `#aa4e44` | Red Minibus series and related figures |
| Railway blue | `#376781` | MTR railway services in recovery and comparison-group charts |
| Bus ochre | `#87632f` | Franchised buses in recovery and comparison-group charts |
| Rule | `#d7dbd2` | Decorative dividers and unobtrusive chart grid lines |

Color always has a second cue. Green Minibuses use a solid line with circular markers. Red Minibuses use a dashed line with diamond markers and an explicit estimate label. MTR share lines are dotted with triangles; franchised buses use a solid line with square markers. December stock uses ink, a dotted line and square markers, distinct from the passenger series. Preserve these differences in legends and accessible tables; recovery bars also have textual category and value labels.

### Contrast

The following ratios are calculated from the specified solid sRGB colors using the WCAG relative-luminance formula. A ratio of 4.5:1 is the minimum for normal-sized text; 3:1 applies to large text and essential graphical distinctions. These token calculations do not replace checking the final rendered combinations, opacity and interaction states.

| Foreground / background | Contrast | Intended use |
| --- | --- | --- |
| Ink / paper | 13.36:1 | Main text and focus outlines |
| Muted / paper | 5.69:1 | Supporting text and axis labels |
| Jade / paper | 6.33:1 | Text, chart marks and accents |
| Coral / paper | 4.91:1 | Text, chart marks and accents |
| Railway blue / paper | 5.58:1 | MTR text and chart marks |
| Bus ochre / paper | 4.95:1 | Franchised-bus text and chart marks |
| Paper / jade | 6.33:1 | Text on a selected jade control |
| Paper / coral | 4.91:1 | Text on a coral surface, where needed |
| Rule / paper | 1.28:1 | Decorative separators only |
| Muted / rule | 4.46:1 | Fails the normal-text threshold; avoid |

Do not use the rule token for essential control boundaries or focus indicators: its contrast against paper is insufficient. Use ink or muted for those boundaries. Coral and bus-ochre text on paper have modest margins above the normal-text threshold, so keep them at full opacity. Recalculate contrast before introducing tinted surfaces or translucent text. The research wash `#eaece3` retains sufficient normal-text contrast for ink (12.33:1), muted (5.25:1) and jade (5.84:1).

## Typography

Self-host Instrument Serif in regular and italic styles for display headings and DM Sans for interface and body text. Retain the font licenses beside the distributed font assets. Font files are static resources; the page should not request fonts from a third-party service at runtime.

Use the serif face for the hero and principal narrative headings. Use DM Sans for navigation, paragraphs, metrics, controls, tables and chart labels. Numbers in the KPI strip should use tabular numerals to keep the percentage signs and decimals visually stable. Display text scales responsively with `clamp()`; readable body text maintains a comfortable line height and a restrained line length. Reserve uppercase lettering for brief metadata, such as the study period, rather than long reading passages.

The hero preserves the approved language exactly:

> **One Industry. Two Different Futures.**
>
> How Hong Kong's Green and Red Minibuses Diverged, 2015–2025.

The second phrase may use italic display type and a restrained accent. Keep one semantic `h1` and a natural reading order even when the heading wraps across several visual lines.

## Publication composition

1. **Navigation:** project identity, Overview, Research, Methodology and the existing GitHub repository. Internal links are anchors in the same HTML document. A research contents navigation introduces Recovery, Landscape, Fleet and Methods.
2. **Hero:** the exact headline and subtitle, a concise explanation of the study, the 2015–2025 period and discreet government-data attribution. The typography introduces the story without stock imagery.
3. **Findings strip:** four figures with visible units, baselines and estimate qualifications. The first three describe 2015–2025 percentage change; the final figure describes 2025 RMB journeys as a percentage of their 2019 level.
4. **Interactive evidence:** one ECharts comparison of annual Green and Red Minibus journeys, with an indexed view, an absolute view and accessible alternatives.
5. **Research narrative:** a concise explanation of the divergent patterns and a link to the existing GitHub findings report.
6. **Recovery chapter:** an annotated bar comparison of five published services against their own 2019 annual journey totals, with the 100% baseline visible and the PLB subtotal explicitly qualified.
7. **Landscape chapter:** four comparison-group share lines, an optional close view of the two minibus components and an inline account of GMB's changing share within PLB. Preserve the distinction between these two denominators without repeating the homepage KPI strip.
8. **Fleet chapter:** a selected minibus service, indexed December licensed stock versus annual journeys, and an alternative annual vehicle-day proxy view. Use one index axis and retain original units in the supporting values.
9. **Methodology chapter and footer:** six expandable explanations covering the scope, calculation rules, transport boundaries, fleet interpretation, validation/revisions and estimates; links to the full documents and attribution to the Hong Kong Transport Department via DATA.GOV.HK.

The chapters form a coherent reading sequence within the approved visual identity. Narrative introductions lead to evidence, supporting values and interpretation notes. The website condenses the research for general readers and links to the full reports rather than copying them. The optional calendar-profile material remains in the published report rather than adding another visualization to this sequence.

## Findings and chart language

| Finding | Display value | Required qualification |
| --- | --- | --- |
| Total minibus annual journeys | −19.51% | 2015–2025 change; includes RMB estimates |
| Green Minibus annual journeys | −11.17% | 2015–2025 change |
| Red Minibus annual journeys | −58.00% | 2015–2025 change; estimated |
| Red Minibus recovery | 49.18% | 2025 as a share of 2019 annual journeys; estimated |

These are formatting targets for values loaded from the validated static data export, not separate analytical calculations in the page markup.

Indexed trends use **each mode's own 2015 annual journeys = 100**. Absolute trends display **annual passenger journeys in millions**. Recovery uses **2019**, not the chart's 2015 denominator. Keep these distinctions visible near the relevant figure or control.

Use chart legends reading “Green Minibuses” and “Red Minibuses · estimated.” Tooltips identify the year, category and displayed measurement, retaining the estimate label. Avoid smoothing that suggests unobserved measurements between the annual observations. The actual data points and the full 2015–2025 coverage remain clear in both chart views.

The central narrative describes published historical change. It does not establish causes, identify individual passengers switching modes or predict future demand. Descriptive period shading, if used, should carry a timing label such as “Disruption period,” rather than a causal claim.

### Chapter measurement boundaries

- **Recovery:** each bar is `2025 journeys / own 2019 journeys × 100`. A visible 100% marker distinguishes matching the benchmark from exceeding it. GMB, RMB and their PLB subtotal are overlapping comparisons, not components to add together.
- **Comparison-group shares:** GMB, RMB, MTR railway services and franchised buses form the four denominator components. PLB is a separate GMB/RMB subtotal. The all-mode line view uses a 0–50% vertical scale; Minibus detail uses 0–20% while retaining the same denominator. Explain this change beside the control.
- **Minibus composition:** GMB's share within PLB uses GMB / (GMB + RMB), distinct from its share in the four-mode group. Present this as an editorial comparison with explicit years and units.
- **Fleet context:** December stock and annual passenger flows each use their own 2015 value = 100. The vehicle-day proxy view uses the existing annual proxy indexed to its own 2015 value; it is not a second axis or a ratio to December stock. Stocks are reported for both GMB and RMB, while RMB journeys and the derived proxy include estimates.
- **Precision and provenance:** all views read the reproducible static export. Round for display only, retain estimation qualifications and refer to [metric provenance](metric_provenance.md) for source columns, denominators and formulas.

## Interaction and accessibility

- Use native buttons for “Indexed · 2015 = 100” and “Absolute · million journeys,” with a visible group label and an accurate `aria-pressed` state. Both remain keyboard operable with a clear focus outline.
- Provide a visibly labeled native year selector for a textual comparison of the chosen annual values. It supplies a touch and keyboard alternative to chart hovering.
- Provide an annual data table with a caption, column headers, units and explicit RMB estimate labeling. It preserves access to every chart observation when canvas interaction is unsuitable.
- Extend the same access pattern to the chapter charts: a native recovery-mode selector, comparison-group year selector and fleet year selector expose useful values without requiring hover. The recovery selector changes the highlighted bar and textual comparison; it does not change the recovery denominator.
- Give the share-focus and fleet-mode/measure buttons accurate pressed states. Fleet controls distinguish GMB/RMB and Stock & journeys / Vehicle-day proxy. The matching legend, description, chart values and supporting table remain consistent with the selection.
- Use native `details` / `summary` for the six methodology explanations and the supporting data tables. Include accessible captions and table headers, with the PLB share column labeled as a subtotal.
- Associate chart instructions and explanatory notes with the visualization. Tooltips supplement the accessible year comparison and table.
- Use semantic landmarks, a skip link and a logical heading hierarchy. Links and buttons have descriptive text and adequate touch targets.
- Treat loading, empty data and data-load failure as distinct states. Explain the state in text and prevent unavailable controls from implying that missing observations equal zero.
- Honor `prefers-reduced-motion`. Disable chart animation and animated scrolling when reduced motion is requested; any other transitions should be brief and purposeful.

## Responsive behavior

Use **680px** and **960px** as the principal layout breakpoints. The wide layout gives the narrative, findings and chart enough room without excessively stretching body text. The intermediate layout reduces columns and adjusts chart spacing. The compact layout keeps the page in a single reading flow, allows navigation and chart controls to wrap, and reduces display type without truncating the headline.

The finding strip moves from four columns to a compact arrangement as space narrows. Its captions and signs remain legible; no figure depends on hovering to reveal its baseline. Each chart keeps a reserved height to limit layout shifts and resizes with its container. Reduce the number of visible year ticks on small screens while retaining all eleven observations and the complete annual tables. Recovery uses compact plotted service labels, with full service definitions available in the selected readout and table. Wrap research legends, chapter links and native controls intentionally. Use responsive label spacing rather than shrinking chart text to an unreadable size.

Body content and controls must fit the viewport without horizontal page scrolling. An overflowing data table may use its own clearly bounded scrolling region. Desktop, tablet and mobile screenshots should document the rendered behavior separately from this intended specification.
