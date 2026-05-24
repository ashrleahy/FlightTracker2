import { useState, useEffect } from "react";
import Papa from "papaparse";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

// ── CONFIG — update this to your repo ────────────────────────────────────────
const CSV_URL = "https://raw.githubusercontent.com/ashrleahy/FlightTracker2/main/flight_log.csv";
const ALERT_THRESHOLD = 500;

// ── Styles ────────────────────────────────────────────────────────────────────
const css = `
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0a0a0a;
    --surface: #111111;
    --border: #1e1e1e;
    --border-bright: #2a2a2a;
    --text: #e8e8e8;
    --muted: #555;
    --pref1: #f0c040;
    --pref2: #4090f0;
    --alert: #40c080;
    --danger: #f05040;
    --font-display: 'Syne', sans-serif;
    --font-mono: 'DM Mono', monospace;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-mono);
    min-height: 100vh;
    padding: 0;
  }

  .app {
    max-width: 1100px;
    margin: 0 auto;
    padding: 48px 24px;
  }

  .header {
    margin-bottom: 48px;
  }

  .header-eyebrow {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
  }

  .header-title {
    font-family: var(--font-display);
    font-size: clamp(2rem, 5vw, 3.5rem);
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.03em;
    color: var(--text);
  }

  .header-title span {
    color: var(--pref1);
  }

  .header-sub {
    margin-top: 12px;
    font-size: 13px;
    color: var(--muted);
    letter-spacing: 0.05em;
  }

  .divider {
    width: 100%;
    height: 1px;
    background: var(--border);
    margin: 32px 0;
  }

  /* Cards */
  .cards {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 40px;
  }

  @media (max-width: 600px) { .cards { grid-template-columns: 1fr; } }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 24px;
    position: relative;
    overflow: hidden;
  }

  .card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
  }

  .card.pref1::before { background: var(--pref1); }
  .card.pref2::before { background: var(--pref2); }
  .card.alert-card::before { background: var(--alert); }

  .card-label {
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 16px;
  }

  .card-price {
    font-family: var(--font-display);
    font-size: 3rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.04em;
  }

  .card.pref1 .card-price { color: var(--pref1); }
  .card.pref2 .card-price { color: var(--pref2); }

  .card-price-unit {
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--muted);
    margin-left: 6px;
    font-weight: 400;
  }

  .card-meta {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .card-meta-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    padding-bottom: 6px;
  }

  .card-meta-row span:last-child {
    color: var(--text);
  }

  .card-alert-badge {
    display: inline-block;
    background: var(--alert);
    color: #000;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 2px;
    margin-top: 12px;
  }

  .card-link {
    display: inline-block;
    margin-top: 14px;
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    text-decoration: none;
    border-bottom: 1px solid var(--border);
    padding-bottom: 2px;
    transition: color 0.15s, border-color 0.15s;
  }

  .card.pref1 .card-link:hover { color: var(--pref1); border-color: var(--pref1); }
  .card.pref2 .card-link:hover { color: var(--pref2); border-color: var(--pref2); }

  /* Chart */
  .chart-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    padding: 28px;
    margin-bottom: 40px;
  }

  .section-label {
    font-size: 10px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 24px;
  }

  /* Table */
  .table-section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 40px;
  }

  .table-header {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  th {
    text-align: left;
    font-size: 10px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted);
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    font-weight: 500;
  }

  td {
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    vertical-align: middle;
  }

  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.02); }

  .pref-badge {
    display: inline-block;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 6px;
    border-radius: 2px;
    font-weight: 500;
  }

  .pref-badge.p1 { background: rgba(240,192,64,0.15); color: var(--pref1); }
  .pref-badge.p2 { background: rgba(64,144,240,0.15); color: var(--pref2); }

  .alert-dot {
    display: inline-block;
    width: 6px; height: 6px;
    background: var(--alert);
    border-radius: 50%;
  }

  .mono { font-family: var(--font-mono); }

  .book-link {
    font-size: 10px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    text-decoration: none;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1px;
  }
  .book-link:hover { color: var(--text); border-color: var(--text); }

  /* Status */
  .status-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    color: var(--muted);
    margin-top: 32px;
  }

  .status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--alert);
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
  }

  .empty {
    text-align: center;
    padding: 60px 24px;
    color: var(--muted);
    font-size: 13px;
  }

  .loading {
    text-align: center;
    padding: 80px 24px;
    color: var(--muted);
    font-size: 12px;
    letter-spacing: 0.1em;
  }

  /* Tooltip */
  .custom-tooltip {
    background: #1a1a1a;
    border: 1px solid var(--border-bright);
    padding: 12px 16px;
    font-size: 12px;
  }

  .tooltip-label {
    color: var(--muted);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }

  .tooltip-row {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 4px;
  }
`;

// ── Custom tooltip ────────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div className="tooltip-label">{label}</div>
      {payload.map((p) => (
        <div key={p.name} className="tooltip-row">
          <span style={{ color: p.color }}>{p.name}</span>
          <span style={{ color: "#e8e8e8" }}>${p.value}</span>
        </div>
      ))}
    </div>
  );
};

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    Papa.parse(CSV_URL, {
      download: true,
      header: true,
      skipEmptyLines: true,
      complete: ({ data }) => {
        setRows(data.reverse()); // newest first
        if (data.length) setLastUpdated(data[data.length - 1]?.timestamp);
        setLoading(false);
      },
      error: (err) => {
        setError(err.message);
        setLoading(false);
      },
    });
  }, []);

  // Latest price per preference
  const latest = (pref) =>
    rows.find((r) => r.preference?.toLowerCase().includes(pref));

  const latest1 = latest("1st");
  const latest2 = latest("2nd");

  // Chart data — group by date, one point per preference
  const chartData = (() => {
    const byDate = {};
    [...rows].reverse().forEach((r) => {
      const day = r.timestamp?.slice(0, 10);
      if (!day) return;
      if (!byDate[day]) byDate[day] = { date: day };
      if (r.preference?.includes("1st")) byDate[day]["1st pref"] = parseFloat(r.price_aud);
      if (r.preference?.includes("2nd")) byDate[day]["2nd pref"] = parseFloat(r.price_aud);
    });
    return Object.values(byDate);
  })();

  const fmt = (n) => n ? `$${parseFloat(n).toFixed(0)}` : "—";

  return (
    <>
      <style>{css}</style>
      <div className="app">
        <div className="header">
          <div className="header-eyebrow">Flight Price Tracker</div>
          <h1 className="header-title">ADL <span>→</span> DPS</h1>
          <div className="header-sub">Adelaide · Bali · 1 adult · Economy · Daily tracking</div>
        </div>

        {loading && <div className="loading">Loading price data...</div>}
        {error && <div className="empty">Could not load CSV — check the repo URL is correct and the file exists.</div>}

        {!loading && !error && rows.length === 0 && (
          <div className="empty">No data yet — run the tracker to populate prices.</div>
        )}

        {!loading && !error && rows.length > 0 && (
          <>
            {/* Price cards */}
            <div className="cards">
              {[
                { pref: "1st", data: latest1, cls: "pref1", label: "1st Preference", dates: "18 Apr → 2 May" },
                { pref: "2nd", data: latest2, cls: "pref2", label: "2nd Preference", dates: "16 Apr → 1 May" },
              ].map(({ data, cls, label, dates }) => (
                <div key={label} className={`card ${cls} ${data?.alert === "YES" ? "alert-card" : ""}`}>
                  <div className="card-label">{label} · {dates}</div>
                  <div className="card-price">
                    {fmt(data?.price_aud)}
                    <span className="card-price-unit">/ adult</span>
                  </div>
                  {data && (
                    <div className="card-meta">
                      <div className="card-meta-row">
                        <span>Airline</span>
                        <span>{data.airline || "—"}</span>
                      </div>
                      <div className="card-meta-row">
                        <span>Duration</span>
                        <span>{data.duration || "—"}</span>
                      </div>
                      <div className="card-meta-row">
                        <span>Stops</span>
                        <span>{data.stops ?? "—"}</span>
                      </div>
                      <div className="card-meta-row">
                        <span>Source</span>
                        <span>{data.source || "—"}</span>
                      </div>
                    </div>
                  )}
                  {data?.alert === "YES" && (
                    <div className="card-alert-badge">⚡ Below threshold</div>
                  )}
                  {data?.jetstar_link && (
                    <a className="card-link" href={data.jetstar_link} target="_blank" rel="noopener">
                      Search on Jetstar →
                    </a>
                  )}
                </div>
              ))}
            </div>

            {/* Chart */}
            {chartData.length > 1 && (
              <div className="chart-section">
                <div className="section-label">Price history — per adult (AUD)</div>
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={chartData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                    <CartesianGrid stroke="#1e1e1e" strokeDasharray="3 3" />
                    <XAxis dataKey="date" tick={{ fill: "#555", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "#555", fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: "11px", color: "#555", paddingTop: "16px" }} />
                    <Line type="monotone" dataKey="1st pref" stroke="#f0c040" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "#f0c040" }} />
                    <Line type="monotone" dataKey="2nd pref" stroke="#4090f0" strokeWidth={2} dot={false} activeDot={{ r: 4, fill: "#4090f0" }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* History table */}
            <div className="table-section">
              <div className="table-header">
                <div className="section-label" style={{ marginBottom: 0 }}>Price history log</div>
              </div>
              <div style={{ overflowX: "auto" }}>
                <table>
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Pref</th>
                      <th>Outbound</th>
                      <th>Return</th>
                      <th>Airline</th>
                      <th>Duration</th>
                      <th>Stops</th>
                      <th>Price</th>
                      <th>Alert</th>
                      <th>Book</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r, i) => (
                      <tr key={i}>
                        <td className="mono" style={{ color: "#555", fontSize: 11 }}>{r.timestamp?.slice(0, 10)}</td>
                        <td>
                          <span className={`pref-badge ${r.preference?.includes("1st") ? "p1" : "p2"}`}>
                            {r.preference?.includes("1st") ? "1st" : "2nd"}
                          </span>
                        </td>
                        <td className="mono">{r.outbound}</td>
                        <td className="mono">{r.return}</td>
                        <td>{r.airline}</td>
                        <td style={{ color: "#888" }}>{r.duration}</td>
                        <td style={{ color: "#888", textAlign: "center" }}>{r.stops}</td>
                        <td className="mono" style={{ color: parseFloat(r.price_aud) < ALERT_THRESHOLD ? "#40c080" : "#e8e8e8", fontWeight: 500 }}>
                          {fmt(r.price_aud)}
                        </td>
                        <td style={{ textAlign: "center" }}>
                          {r.alert === "YES" && <span className="alert-dot" title="Below threshold" />}
                        </td>
                        <td>
                          {r.jetstar_link && (
                            <a className="book-link" href={r.jetstar_link} target="_blank" rel="noopener">Jetstar</a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="status-bar">
              <span className="status-dot" />
              <span>Last updated {lastUpdated?.slice(0, 10) || "—"} · Updates daily at 08:30 ACST</span>
            </div>
          </>
        )}
      </div>
    </>
  );
}
