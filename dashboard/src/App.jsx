import { useState, useEffect } from "react";
import Papa from "papaparse";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

const CSV_URL = "https://raw.githubusercontent.com/ashrleahy/FlightTracker2/main/flight_log.csv";
const ALERT_THRESHOLD = 500;

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Bebas+Neue&family=JetBrains+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #0d0d0f;
    --surface: #16161a;
    --surface2: #1e1e24;
    --border: #2a2a35;
    --text: #f0f0f5;
    --text-secondary: #9090a8;
    --text-muted: #55556a;
    --pref1: #ffcc00;
    --pref1-dim: rgba(255,204,0,0.12);
    --pref2: #4da6ff;
    --pref2-dim: rgba(77,166,255,0.12);
    --alert: #00e090;
    --alert-dim: rgba(0,224,144,0.1);
    --font-display: 'Bebas Neue', sans-serif;
    --font-body: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font-body);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
  }

  .app {
    max-width: 1080px;
    margin: 0 auto;
    padding: 56px 28px;
  }

  /* ── Header ── */
  .header {
    margin-bottom: 52px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 32px;
  }

  .eyebrow {
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 10px;
  }

  .title {
    font-family: var(--font-display);
    font-size: clamp(3rem, 8vw, 5.5rem);
    line-height: 0.95;
    letter-spacing: 0.02em;
    color: var(--text);
  }

  .title .arrow { color: var(--pref1); }

  .subtitle {
    margin-top: 14px;
    font-size: 13px;
    color: var(--text-secondary);
    font-family: var(--font-mono);
    letter-spacing: 0.04em;
  }

  /* ── Cards ── */
  .cards {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    margin-bottom: 32px;
  }
  @media (max-width: 580px) { .cards { grid-template-columns: 1fr; } }

  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 28px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s;
  }
  .card:hover { border-color: #3a3a48; }

  .card-accent {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 8px 8px 0 0;
  }
  .card.p1 .card-accent { background: linear-gradient(90deg, var(--pref1), rgba(255,204,0,0.3)); }
  .card.p2 .card-accent { background: linear-gradient(90deg, var(--pref2), rgba(77,166,255,0.3)); }

  .card-label {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 20px;
  }

  .card-price-row {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 4px;
  }

  .card-price {
    font-family: var(--font-display);
    font-size: 4rem;
    line-height: 1;
    letter-spacing: 0.02em;
  }
  .card.p1 .card-price { color: var(--pref1); }
  .card.p2 .card-price { color: var(--pref2); }

  .card-price-unit {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-muted);
  }

  .card-dates {
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 20px;
  }

  .card-divider {
    height: 1px;
    background: var(--border);
    margin: 16px 0;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .meta-item {}

  .meta-key {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 3px;
  }

  .meta-val {
    font-size: 13px;
    color: var(--text);
    font-weight: 500;
  }

  .alert-pill {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--alert-dim);
    border: 1px solid rgba(0,224,144,0.3);
    color: var(--alert);
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 4px 10px;
    border-radius: 4px;
    margin-top: 16px;
  }

  .alert-dot-pulse {
    width: 6px; height: 6px;
    background: var(--alert);
    border-radius: 50%;
    animation: pulse 1.8s ease-in-out infinite;
  }

  .book-btn {
    display: inline-block;
    margin-top: 16px;
    padding: 8px 16px;
    border-radius: 5px;
    font-family: var(--font-mono);
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    text-decoration: none;
    font-weight: 500;
    transition: opacity 0.15s;
  }
  .book-btn:hover { opacity: 0.8; }
  .card.p1 .book-btn { background: var(--pref1-dim); color: var(--pref1); border: 1px solid rgba(255,204,0,0.25); }
  .card.p2 .book-btn { background: var(--pref2-dim); color: var(--pref2); border: 1px solid rgba(77,166,255,0.25); }

  /* ── Chart ── */
  .section {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 28px;
    margin-bottom: 24px;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
  }

  .section-title {
    font-family: var(--font-display);
    font-size: 1.6rem;
    letter-spacing: 0.04em;
    color: var(--text);
  }

  .legend {
    display: flex;
    gap: 16px;
  }

  .legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-secondary);
    letter-spacing: 0.08em;
  }

  .legend-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
  }

  /* ── Table ── */
  .table-wrap { overflow-x: auto; }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }

  th {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--text-muted);
    text-align: left;
    padding: 8px 14px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }

  td {
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
    white-space: nowrap;
  }

  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.015); color: var(--text); }

  td.price-cell {
    font-family: var(--font-mono);
    font-weight: 500;
    font-size: 13px;
  }

  td.price-alert { color: var(--alert) !important; }
  td.mono { font-family: var(--font-mono); font-size: 11px; }

  .badge {
    display: inline-block;
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 2px 7px;
    border-radius: 3px;
    font-weight: 500;
  }
  .badge.p1 { background: var(--pref1-dim); color: var(--pref1); }
  .badge.p2 { background: var(--pref2-dim); color: var(--pref2); }

  .tbl-link {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-muted);
    text-decoration: none;
    letter-spacing: 0.06em;
    border-bottom: 1px solid var(--border);
    padding-bottom: 1px;
    transition: color 0.15s;
  }
  .tbl-link:hover { color: var(--text); }

  /* ── Footer ── */
  .footer {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-top: 32px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-muted);
  }

  .status-dot {
    width: 7px; height: 7px;
    background: var(--alert);
    border-radius: 50%;
    animation: pulse 2s ease-in-out infinite;
    flex-shrink: 0;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.4; transform: scale(0.8); }
  }

  .empty, .loading {
    text-align: center;
    padding: 80px 24px;
    font-family: var(--font-mono);
    font-size: 13px;
    color: var(--text-muted);
    letter-spacing: 0.08em;
  }

  .tooltip-box {
    background: #1e1e26;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 12px 16px;
    font-family: var(--font-mono);
    font-size: 12px;
  }
  .tooltip-date {
    color: var(--text-muted);
    font-size: 10px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 8px;
  }
  .tooltip-row {
    display: flex;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 3px;
  }
`;

const Tooltip_ = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="tooltip-box">
      <div className="tooltip-date">{label}</div>
      {payload.map(p => p.value && (
        <div key={p.name} className="tooltip-row">
          <span style={{ color: p.color }}>{p.name}</span>
          <span style={{ color: "#f0f0f5" }}>${p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function App() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    Papa.parse(CSV_URL, {
      download: true, header: true, skipEmptyLines: true,
      complete: ({ data }) => { setRows(data.reverse()); setLoading(false); },
      error: (err) => { setError(err.message); setLoading(false); },
    });
  }, []);

  const latest = (n) => rows.find(r => r.preference?.includes(n));
  const l1 = latest("1st");
  const l2 = latest("2nd");

  const chartData = (() => {
    const map = {};
    [...rows].reverse().forEach(r => {
      const d = r.timestamp?.slice(0, 10);
      if (!d || !r.price_aud) return;
      if (!map[d]) map[d] = { date: d };
      if (r.preference?.includes("1st")) map[d]["1st"] = parseFloat(r.price_aud);
      if (r.preference?.includes("2nd")) map[d]["2nd"] = parseFloat(r.price_aud);
    });
    return Object.values(map);
  })();

  const fmt = n => n ? `$${parseFloat(n).toFixed(0)}` : "—";
  const lastDate = [...rows].reverse().find(r => r.timestamp)?.timestamp?.slice(0,10);

  return (
    <>
      <style>{css}</style>
      <div className="app">
        <div className="header">
          <div className="eyebrow">Flight Price Tracker · Adelaide → Bali</div>
          <h1 className="title">ADL <span className="arrow">→</span> DPS</h1>
          <div className="subtitle">1 adult · Economy · Direct or 1 stop · Updated daily 08:30 ACST</div>
        </div>

        {loading && <div className="loading">Loading price data...</div>}
        {error && <div className="empty">Could not load data — check repo URL and CSV exists.</div>}
        {!loading && !error && rows.length === 0 && <div className="empty">No data yet — run the tracker first.</div>}

        {!loading && !error && rows.length > 0 && (<>

          <div className="cards">
            {[
              { n: "1st", label: "1st Preference", dates: "18 Apr → 2 May 2027", data: l1, cls: "p1" },
              { n: "2nd", label: "2nd Preference", dates: "16 Apr → 1 May 2027", data: l2, cls: "p2" },
            ].map(({ label, dates, data, cls }) => (
              <div key={label} className={`card ${cls}`}>
                <div className="card-accent" />
                <div className="card-label">{label}</div>
                <div className="card-price-row">
                  <div className="card-price">{fmt(data?.price_aud)}</div>
                  <div className="card-price-unit">/ adult AUD</div>
                </div>
                <div className="card-dates">{dates}</div>
                <div className="card-divider" />
                <div className="meta-grid">
                  <div className="meta-item">
                    <div className="meta-key">Airline</div>
                    <div className="meta-val">{data?.airline || "—"}</div>
                  </div>
                  <div className="meta-item">
                    <div className="meta-key">Duration</div>
                    <div className="meta-val">{data?.duration || "—"}</div>
                  </div>
                  <div className="meta-item">
                    <div className="meta-key">Stops</div>
                    <div className="meta-val">{data?.stops ?? "—"}</div>
                  </div>
                  <div className="meta-item">
                    <div className="meta-key">Source</div>
                    <div className="meta-val">{data?.source || "—"}</div>
                  </div>
                </div>
                {data?.alert === "YES" && (
                  <div className="alert-pill">
                    <span className="alert-dot-pulse" />
                    Below alert threshold
                  </div>
                )}
                {data?.jetstar_link && (
                  <a className="book-btn" href={data.jetstar_link} target="_blank" rel="noopener">
                    Search Jetstar →
                  </a>
                )}
              </div>
            ))}
          </div>

          {chartData.length > 0 && (
            <div className="section">
              <div className="section-header">
                <div className="section-title">Price History</div>
                <div className="legend">
                  <div className="legend-item"><div className="legend-dot" style={{background:"#ffcc00"}} />1st pref</div>
                  <div className="legend-item"><div className="legend-dot" style={{background:"#4da6ff"}} />2nd pref</div>
                </div>
              </div>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={chartData} margin={{ top: 5, right: 8, left: -8, bottom: 0 }}>
                  <CartesianGrid stroke="#2a2a35" strokeDasharray="4 4" vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: "#55556a", fontSize: 10, fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} />
                  <YAxis tick={{ fill: "#55556a", fontSize: 10, fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} tickFormatter={v => `$${v}`} width={55} />
                  <Tooltip content={<Tooltip_ />} />
                  <ReferenceLine y={ALERT_THRESHOLD} stroke="rgba(0,224,144,0.25)" strokeDasharray="4 4" label={{ value: "Alert", fill: "#00e090", fontSize: 9, fontFamily: "JetBrains Mono" }} />
                  <Line type="monotone" dataKey="1st" stroke="#ffcc00" strokeWidth={2} dot={{ r: 3, fill: "#ffcc00", strokeWidth: 0 }} activeDot={{ r: 5, fill: "#ffcc00", strokeWidth: 0 }} connectNulls />
                  <Line type="monotone" dataKey="2nd" stroke="#4da6ff" strokeWidth={2} dot={{ r: 3, fill: "#4da6ff", strokeWidth: 0 }} activeDot={{ r: 5, fill: "#4da6ff", strokeWidth: 0 }} connectNulls />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          <div className="section">
            <div className="section-header">
              <div className="section-title">History Log</div>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Pref</th>
                    <th>Out</th>
                    <th>Return</th>
                    <th>Days</th>
                    <th>Airline</th>
                    <th>Duration</th>
                    <th>Stops</th>
                    <th>Price</th>
                    <th>Book</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={i}>
                      <td className="mono">{r.timestamp?.slice(0,10)}</td>
                      <td><span className={`badge ${r.preference?.includes("1st") ? "p1" : "p2"}`}>{r.preference?.includes("1st") ? "1st" : "2nd"}</span></td>
                      <td className="mono">{r.outbound}</td>
                      <td className="mono">{r.return}</td>
                      <td className="mono">{r.trip_days}</td>
                      <td style={{color:"var(--text)"}}>{r.airline}</td>
                      <td>{r.duration}</td>
                      <td className="mono" style={{textAlign:"center"}}>{r.stops}</td>
                      <td className={`price-cell ${parseFloat(r.price_aud) < ALERT_THRESHOLD ? "price-alert" : ""}`}>{fmt(r.price_aud)}</td>
                      <td>{r.jetstar_link && <a className="tbl-link" href={r.jetstar_link} target="_blank" rel="noopener">Jetstar ↗</a>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="footer">
            <span className="status-dot" />
            <span>Last tracked {lastDate || "—"} · Data via Kiwi.com · Verify prices on Jetstar before booking</span>
          </div>

        </>)}
      </div>
    </>
  );
}
