import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  annualSeries,
  percentage,
  validateResearchData,
  yearRows,
} from "../src/data.js";
import { chartOptions, tooltipMarkup } from "../src/chart.js";

const research = JSON.parse(
  readFileSync(
    new URL("../public/data/research.json", import.meta.url),
    "utf8",
  ),
);
const years = Array.from({ length: 11 }, (_, offset) => 2015 + offset);
const copy = () => structuredClone(research);
const close = (actual, expected) =>
  assert.ok(
    Math.abs(actual - expected) < 1e-9,
    `${actual} differs from ${expected}`,
  );

test("the genuine research export satisfies the browser data contract", () => {
  assert.equal(validateResearchData(research), research);
});

test("relative view compares each service against its own 2015 passenger total", () => {
  const indexed = chartOptions(research, "index");
  for (const series of indexed.series) {
    assert.equal(series.data[0], 100, `${series.id} must begin at 100`);
    const baseline = research.annual.find(
      (row) => row.mode === series.id && row.year === 2015,
    ).journeys_thousands;
    for (const [position, year] of years.entries()) {
      const annual = research.annual.find(
        (row) => row.mode === series.id && row.year === year,
      );
      close(
        series.data[position],
        (annual.journeys_thousands / baseline) * 100,
      );
    }
  }
  close(indexed.series[0].data.at(-1), 88.82566993179198);
  close(indexed.series[1].data.at(-1), 41.99626645546396);
});

test("absolute view retains annual journey volume in millions rather than rebasing both services", () => {
  const absolute = chartOptions(research, "absolute");
  close(absolute.series[0].data[0], 558.174697);
  close(absolute.series[1].data[0], 120.826736);
  close(absolute.series[0].data.at(-1), 495.802414);
  close(absolute.series[1].data.at(-1), 50.742718);
  for (const series of absolute.series) {
    for (const [position, year] of years.entries()) {
      const annual = research.annual.find(
        (row) => row.mode === series.id && row.year === year,
      );
      close(series.data[position] * 1000, annual.journeys_thousands);
    }
  }
  assert.match(absolute.aria.description, /millions of passenger journeys/);
});

test("both views sort all annual points chronologically even if the source array is reversed", () => {
  const shuffled = copy();
  shuffled.annual.reverse();
  for (const mode of ["GMB", "RMB"]) {
    for (const view of ["index", "absolute"]) {
      assert.deepEqual(
        annualSeries(shuffled, mode, view),
        annualSeries(research, mode, view),
      );
      assert.equal(annualSeries(shuffled, mode, view).length, 11);
    }
  }
});

test("the four displayed headline percentages exactly retain the approved rounding and signs", () => {
  assert.deepEqual(
    Object.values(research.kpis).map((value) => percentage(value)),
    ["−19.51%", "−11.17%", "−58.00%", "49.18%"],
  );
  assert.equal(percentage(research.kpis.rmb_change_pct, true), "58.00%");
  assert.equal(percentage(research.kpis.rmb_recovery_2019_pct, true), "49.18%");
});

test("year lookup consistently returns the reported Green and estimated Red observations", () => {
  for (const year of years) {
    const [gmb, rmb] = yearRows(research, year);
    assert.deepEqual([gmb.mode, rmb.mode], ["GMB", "RMB"]);
    assert.deepEqual([gmb.year, rmb.year], [year, year]);
    assert.deepEqual(
      [gmb.includes_estimates, rmb.includes_estimates],
      [false, true],
    );
  }
});

const invalidCases = [
  ["missing research export", () => undefined],
  [
    "unsupported schema",
    (data) => {
      data.schema_version = 2;
    },
  ],
  [
    "missing annual observations",
    (data) => {
      delete data.annual;
    },
  ],
  [
    "empty annual observations",
    (data) => {
      data.annual = [];
    },
  ],
  [
    "missing annual year",
    (data) => {
      data.annual.pop();
    },
  ],
  [
    "duplicate annual observation replacing a missing point",
    (data) => {
      data.annual[1] = { ...data.annual[0] };
    },
  ],
  [
    "invalid service identifier",
    (data) => {
      data.annual[0].mode = "PLB";
    },
  ],
  [
    "year outside the complete study period",
    (data) => {
      data.annual[0].year = 2014;
    },
  ],
  [
    "NaN annual volume",
    (data) => {
      data.annual[0].journeys_thousands = NaN;
    },
  ],
  [
    "NaN relative index",
    (data) => {
      data.annual[0].index_2015 = NaN;
    },
  ],
  [
    "missing annual volume",
    (data) => {
      delete data.annual[0].journeys_thousands;
    },
  ],
  [
    "zero 2015 baseline",
    (data) => {
      data.annual[0].journeys_thousands = 0;
    },
  ],
  [
    "negative 2015 baseline",
    (data) => {
      data.annual[1].journeys_thousands = -1;
    },
  ],
  [
    "2015 baseline index other than 100",
    (data) => {
      data.annual[0].index_2015 = 99;
    },
  ],
  [
    "later index inconsistent with the own-service baseline",
    (data) => {
      data.annual.at(-1).index_2015 = 100;
    },
  ],
  [
    "Red journey wrongly marked observed",
    (data) => {
      data.annual[1].includes_estimates = false;
    },
  ],
  [
    "Green journey wrongly marked estimated",
    (data) => {
      data.annual[0].includes_estimates = true;
    },
  ],
  [
    "Red measurement basis wrongly marked reported",
    (data) => {
      data.annual[1].measurement_basis = "reported";
    },
  ],
  [
    "Green measurement basis wrongly marked estimated",
    (data) => {
      data.annual[0].measurement_basis = "estimated";
    },
  ],
  [
    "missing research KPI",
    (data) => {
      delete data.kpis.gmb_change_pct;
    },
  ],
  [
    "NaN research KPI",
    (data) => {
      data.kpis.rmb_recovery_2019_pct = NaN;
    },
  ],
  [
    "empty source date",
    (data) => {
      data.provenance.snapshot_retrieved_on = "";
    },
  ],
  [
    "missing source vintage",
    (data) => {
      delete data.provenance;
    },
  ],
];

for (const [description, mutate] of invalidCases) {
  test(`data validation rejects ${description}`, () => {
    const candidate = copy();
    const replacement = mutate(candidate);
    assert.throws(() =>
      validateResearchData(
        description === "missing research export" ? replacement : candidate,
      ),
    );
  });
}

test("unsupported chart views and non-finite percentages fail clearly", () => {
  assert.throws(
    () => annualSeries(research, "GMB", "unknown"),
    /Unknown chart view/,
  );
  for (const value of [NaN, Infinity, undefined])
    assert.throws(() => percentage(value), /Invalid percentage/);
});

for (const view of ["index", "absolute"]) {
  test(`${view} tooltip identifies every year, both services, Red estimation, and absolute units`, () => {
    for (const year of years) {
      const markup = tooltipMarkup(research, String(year), view);
      assert.match(markup, new RegExp(`tooltip-year">${year}</div>`));
      assert.match(markup, /Green Minibuses/);
      assert.match(markup, /Red Minibuses · est\./);
      assert.match(
        markup,
        /(?:million(?:s)?(?: of passenger)? journeys|passenger journeys · millions)/i,
      );
      const [gmb, rmb] = yearRows(research, year);
      assert.ok(markup.includes((gmb.journeys_thousands / 1000).toFixed(2)));
      assert.ok(markup.includes((rmb.journeys_thousands / 1000).toFixed(2)));
      if (view === "index") {
        assert.ok(markup.includes(gmb.index_2015.toFixed(2)));
        assert.ok(markup.includes(rmb.index_2015.toFixed(2)));
        assert.match(markup, /own 2015 = 100/);
      }
    }
  });

  test(`${view} chart preserves all eleven points and both endpoint labels on mobile`, () => {
    const desktop = chartOptions(research, view);
    const mobile = chartOptions(research, view, { mobile: true });
    assert.deepEqual(mobile.xAxis.data, years.map(String));
    assert.deepEqual(mobile.xAxis.data, desktop.xAxis.data);
    assert.equal(mobile.xAxis.axisLabel.showMinLabel, true);
    assert.equal(mobile.xAxis.axisLabel.showMaxLabel, true);
    assert.ok(
      mobile.xAxis.axisLabel.interval > desktop.xAxis.axisLabel.interval,
    );
    for (const [position, series] of mobile.series.entries()) {
      assert.equal(series.data.length, 11);
      assert.deepEqual(series.data, desktop.series[position].data);
    }
  });
}

test("tooltip formatter uses the selected annual category rather than an unrelated array position", () => {
  const options = chartOptions(research, "index");
  assert.equal(
    options.tooltip.formatter([{ axisValue: "2025" }]),
    tooltipMarkup(research, 2025, "index"),
  );
  assert.equal(options.tooltip.formatter([]), "");
  assert.equal(tooltipMarkup(research, 2014, "index"), "");
});

test("reduced-motion preference disables chart animation in both views and viewport layouts", () => {
  for (const view of ["index", "absolute"]) {
    for (const mobile of [false, true]) {
      assert.equal(
        chartOptions(research, view, { mobile, reducedMotion: true }).animation,
        false,
      );
      assert.equal(
        chartOptions(research, view, { mobile, reducedMotion: false })
          .animation,
        true,
      );
    }
  }
});

test("Red estimates remain distinguishable without relying on color alone", () => {
  for (const view of ["index", "absolute"]) {
    const [gmb, rmb] = chartOptions(research, view).series;
    assert.notEqual(gmb.lineStyle.type, rmb.lineStyle.type);
    assert.notEqual(gmb.symbol, rmb.symbol);
    assert.notEqual(gmb.lineStyle.color, rmb.lineStyle.color);
    assert.match(rmb.name, /estimated/);
    assert.equal(gmb.smooth, false);
    assert.equal(rmb.smooth, false);
  }
});
