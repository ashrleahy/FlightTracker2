import { useState, useEffect } from "react";
import Papa from "papaparse";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

const FLIGHT_CSV = "https://raw.githubusercontent.com/ashrleahy/FlightTracker2/main/flight_log.csv";
const HOTEL_CSV  = "https://raw.githubusercontent.com/ashrleahy/FlightTracker2/main/hotel_log.csv";
const FLIGHT_ALERT = 500;

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
    --hotel1: #ff8c42;
    --hotel1-dim: rgba(255,140,66,0.12);
    --hotel2: #a78bfa;
    --hotel2-dim: rgba(167,139,250,0.12);
    --hotel3: #34d399;
    --hotel3-dim: rgba(52,211,153,0.12);
    --alert: #00e090;
    --alert-dim: rgba(0,224,144,0.1);
    --font-display: 'Bebas Neue', sans-serif;
    --font-body: 'Inter', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
  }
  body { background: var(--bg); color: var(--text); font-family: var(--font-body); min-height: 100vh; -webkit-font-smoothing: antialiased; }
  .app { max-width: 1080px; margin: 0 auto; padding: 56px 28px; }

  /* Header */
  .header { margin-bottom: 40px; border-bottom: 1px solid var(--border); padding-bottom: 28px; }
  .eyebrow { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--text-muted); margin-bottom: 10px; }
  .title { font-family: var(--font-display); font-size: clamp(3rem, 8vw, 5.5rem); line-height: 0.95; letter-spacing: 0.02em; color: var(--text); }
  .title .arrow { color: var(--pref1); }
  .subtitle { margin-top: 14px; font-size: 13px; color: var(--text-secondary); font-family: var(--font-mono); letter-spacing: 0.04em; }

  /* Tabs */
  .tabs { display: flex; gap: 0; margin-bottom: 36px; border-bottom: 1px solid var(--border); }
  .tab { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; padding: 12px 24px; cursor: pointer; color: var(--text-muted); border-bottom: 2px solid transparent; margin-bottom: -1px; background: none; border-top: none; border-left: none; border-right: none; transition: color 0.15s; }
  .tab:hover { color: var(--text-secondary); }
  .tab.active { color: var(--text); border-bottom-color: var(--pref1); }

  /* Cards */
  .cards { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 32px; }
  .cards-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 32px; }
  @media (max-width: 700px) { .cards, .cards-3 { grid-template-columns: 1fr; } }
  .card { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 28px; position: relative; overflow: hidden; transition: border-color 0.2s; }
  .card:hover { border-color: #3a3a48; }
  .card-accent { position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 8px 8px 0 0; }
  .card.c0 .card-accent { background: linear-gradient(90deg, var(--hotel1), rgba(255,140,66,0.3)); }
  .card.c1 .card-accent { background: linear-gradient(90deg, var(--hotel2), rgba(167,139,250,0.3)); }
  .card.c2 .card-accent { background: linear-gradient(90deg, var(--hotel3), rgba(52,211,153,0.3)); }
  .card.p1 .card-accent { background: linear-gradient(90deg, var(--pref1), rgba(255,204,0,0.3)); }
  .card.p2 .card-accent { background: linear-gradient(90deg, var(--pref2), rgba(77,166,255,0.3)); }
  .card-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--text-muted); margin-bottom: 20px; }
  .card-price { font-family: var(--font-display); font-size: 3.5rem; line-height: 1; letter-spacing: 0.02em; }
  .card.p1 .card-price { color: var(--pref1); }
  .card.p2 .card-price { color: var(--pref2); }
  .card.c0 .card-price { color: var(--hotel1); }
  .card.c1 .card-price { color: var(--hotel2); }
  .card.c2 .card-price { color: var(--hotel3); }
  .card-price-unit { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); margin-left: 4px; }
  .card-dates { font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary); margin: 8px 0 20px; }
  .card-divider { height: 1px; background: var(--border); margin: 16px 0; }
  .meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .meta-key { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-muted); margin-bottom: 3px; }
  .meta-val { font-size: 13px; color: var(--text); font-weight: 500; }
  .alert-pill { display: inline-flex; align-items: center; gap: 6px; background: var(--alert-dim); border: 1px solid rgba(0,224,144,0.3); color: var(--alert); font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; padding: 4px 10px; border-radius: 4px; margin-top: 16px; }
  .alert-dot-pulse { width: 6px; height: 6px; background: var(--alert); border-radius: 50%; animation: pulse 1.8s ease-in-out infinite; }
  .book-btn { display: inline-block; margin-top: 16px; padding: 8px 16px; border-radius: 5px; font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; text-decoration: none; font-weight: 500; transition: opacity 0.15s; }
  .book-btn:hover { opacity: 0.8; }
  .card.p1 .book-btn { background: var(--pref1-dim); color: var(--pref1); border: 1px solid rgba(255,204,0,0.25); }
  .card.p2 .book-btn { background: var(--pref2-dim); color: var(--pref2); border: 1px solid rgba(77,166,255,0.25); }
  .card.c0 .book-btn { background: var(--hotel1-dim); color: var(--hotel1); border: 1px solid rgba(255,140,66,0.25); }
  .card.c1 .book-btn { background: var(--hotel2-dim); color: var(--hotel2); border: 1px solid rgba(167,139,250,0.25); }
  .card.c2 .book-btn { background: var(--hotel3-dim); color: var(--hotel3); border: 1px solid rgba(52,211,153,0.25); }

  /* Section */
  .section { background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 28px; margin-bottom: 24px; }
  .section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
  .section-title { font-family: var(--font-display); font-size: 1.6rem; letter-spacing: 0.04em; color: var(--text); }
  .legend { display: flex; gap: 16px; flex-wrap: wrap; }
  .legend-item { display: flex; align-items: center; gap: 6px; font-family: var(--font-mono); font-size: 10px; color: var(--text-secondary); letter-spacing: 0.08em; }
  .legend-dot { width: 8px; height: 8px; border-radius: 50%; }

  /* Table */
  .table-wrap { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-muted); text-align: left; padding: 8px 14px; border-bottom: 1px solid var(--border); white-space: nowrap; }
  td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--text-secondary); white-space: nowrap; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,0.015); color: var(--text); }
  td.mono { font-family: var(--font-mono); font-size: 11px; }
  td.price-cell { font-family: var(--font-mono); font-weight: 500; font-size: 13px; }
  td.price-alert { color: var(--alert) !important; }
  .badge { display: inline-block; font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.1em; text-transform: uppercase; padding: 2px 7px; border-radius: 3px; font-weight: 500; }
  .badge.p1 { background: var(--pref1-dim); color: var(--pref1); }
  .badge.p2 { background: var(--pref2-dim); color: var(--pref2); }
  .badge.h0 { background: var(--hotel1-dim); color: var(--hotel1); }
  .badge.h1 { background: var(--hotel2-dim); color: var(--hotel2); }
  .badge.h2 { background: var(--hotel3-dim); color: var(--hotel3); }
  .tbl-link { font-family: var(--font-mono); font-size: 10px; color: var(--text-muted); text-decoration: none; letter-spacing: 0.06em; border-bottom: 1px solid var(--border); padding-bottom: 1px; transition: color 0.15s; }
  .tbl-link:hover { color: var(--text); }

  /* Footer */
  .footer { display: flex; align-items: center; gap: 10px; margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--border); font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }
  .status-dot { width: 7px; height: 7px; background: var(--alert); border-radius: 50%; animation: pulse 2s ease-in-out infinite; flex-shrink: 0; }
  @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.8); } }
  .empty, .loading { text-align: center; padding: 80px 24px; font-family: var(--font-mono); font-size: 13px; color: var(--text-muted); letter-spacing: 0.08em; }
  .tooltip-box { background: #1e1e26; border: 1px solid var(--border); border-radius: 6px; padding: 12px 16px; font-family: var(--font-mono); font-size: 12px; }
  .tooltip-date { color: var(--text-muted); font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px; }
  .tooltip-row { display: flex; justify-content: space-between; gap: 20px; margin-bottom: 3px; }

  /* Trip summary */
  .trip-summary { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 20px 24px; margin-bottom: 32px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px; }
  .trip-total-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-muted); margin-bottom: 4px; }
  .trip-total-val { font-family: var(--font-display); font-size: 2.2rem; color: var(--alert); letter-spacing: 0.02em; }
  .trip-breakdown { display: flex; gap: 24px; flex-wrap: wrap; }
  .trip-item { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); }
  .trip-item span { color: var(--text); font-weight: 500; }
`;

const TooltipBox = ({ active, payload, label }) => {
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

const fmt = n => n ? `$${parseFloat(n).toFixed(0)}` : "—";

const HOTEL_COLORS = ["#ff8c42", "#a78bfa", "#34d399"];
const HOTEL_NAMES  = ["Andaz Bali", "Villa Tokay", "BASK Gili Meno"];

// ── Flights Tab ───────────────────────────────────────────────────────────────
function FlightsTab({ rows }) {
  const latest = pref => rows.find(r => r.preference?.includes(pref));
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

  return (
    <>
      <div className="cards">
        {[
          { label: "1st Preference", dates: "18 Apr → 2 May 2027", data: l1, cls: "p1" },
          { label: "2nd Preference", dates: "16 Apr → 1 May 2027", data: l2, cls: "p2" },
        ].map(({ label, dates, data, cls }) => (
          <div key={label} className={`card ${cls}`}>
            <div className="card-accent" />
            <div className="card-label">{label}</div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <div className="card-price">{fmt(data?.price_aud)}</div>
              <span className="card-price-unit">/ adult AUD</span>
            </div>
            <div className="card-dates">{dates}</div>
            <div className="card-divider" />
            <div className="meta-grid">
              <div><div className="meta-key">Airline</div><div className="meta-val">{data?.airline || "—"}</div></div>
              <div><div className="meta-key">Duration</div><div className="meta-val">{data?.duration || "—"}</div></div>
              <div><div className="meta-key">Stops</div><div className="meta-val">{data?.stops ?? "—"}</div></div>
              <div><div className="meta-key">Source</div><div className="meta-val">{data?.source || "—"}</div></div>
            </div>
            {data?.alert === "YES" && <div className="alert-pill"><span className="alert-dot-pulse" />Below threshold</div>}
            {data?.jetstar_link && <a className="book-btn" href={data.jetstar_link} target="_blank" rel="noopener">Search Jetstar →</a>}
          </div>
        ))}
      </div>

      {chartData.length > 1 && (
        <div className="section">
          <div className="section-header">
            <div className="section-title">Price History</div>
            <div className="legend">
              <div className="legend-item"><div className="legend-dot" style={{background:"#ffcc00"}} />1st pref</div>
              <div className="legend-item"><div className="legend-dot" style={{background:"#4da6ff"}} />2nd pref</div>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={chartData} margin={{ top: 5, right: 8, left: -8, bottom: 0 }}>
              <CartesianGrid stroke="#2a2a35" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "#55556a", fontSize: 10, fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: "#55556a", fontSize: 10, fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} tickFormatter={v => `$${v}`} width={55} />
              <Tooltip content={<TooltipBox />} />
              <ReferenceLine y={FLIGHT_ALERT} stroke="rgba(0,224,144,0.25)" strokeDasharray="4 4" />
              <Line type="monotone" dataKey="1st" stroke="#ffcc00" strokeWidth={2} dot={{ r: 3, fill: "#ffcc00", strokeWidth: 0 }} activeDot={{ r: 5 }} connectNulls />
              <Line type="monotone" dataKey="2nd" stroke="#4da6ff" strokeWidth={2} dot={{ r: 3, fill: "#4da6ff", strokeWidth: 0 }} activeDot={{ r: 5 }} connectNulls />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="section">
        <div className="section-header"><div className="section-title">History Log</div></div>
        <div className="table-wrap">
          <table>
            <thead><tr>
              <th>Date</th><th>Pref</th><th>Out</th><th>Return</th><th>Airline</th><th>Duration</th><th>Stops</th><th>Price</th><th>Book</th>
            </tr></thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i}>
                  <td className="mono">{r.timestamp?.slice(0,10)}</td>
                  <td><span className={`badge ${r.preference?.includes("1st") ? "p1" : "p2"}`}>{r.preference?.includes("1st") ? "1st" : "2nd"}</span></td>
                  <td className="mono">{r.outbound}</td>
                  <td className="mono">{r.return}</td>
                  <td style={{color:"var(--text)"}}>{r.airline}</td>
                  <td>{r.duration}</td>
                  <td className="mono" style={{textAlign:"center"}}>{r.stops}</td>
                  <td className={`price-cell ${parseFloat(r.price_aud) < FLIGHT_ALERT ? "price-alert" : ""}`}>{fmt(r.price_aud)}</td>
                  <td>{r.jetstar_link && <a className="tbl-link" href={r.jetstar_link} target="_blank" rel="noopener">Jetstar ↗</a>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// ── Hotels Tab ────────────────────────────────────────────────────────────────
function HotelsTab({ rows }) {
  const latest = name => rows.find(r => r.hotel === name);

  const hotels = HOTEL_NAMES.map((name, i) => ({
    name,
    idx: i,
    data: latest(name),
    color: HOTEL_COLORS[i],
  }));

  // Trip total (latest price per hotel summed)
  const tripTotal = hotels.reduce((sum, h) => {
    const p = parseFloat(h.data?.price_total_aud || 0);
    return sum + p;
  }, 0);

  // Chart — price per night over time per hotel
  const chartData = (() => {
    const map = {};
    [...rows].reverse().forEach(r => {
      const d = r.timestamp?.slice(0, 10);
      if (!d || !r.price_per_night_aud) return;
      if (!map[d]) map[d] = { date: d };
      map[d][r.hotel] = parseFloat(r.price_per_night_aud);
    });
    return Object.values(map);
  })();

  return (
    <>
      {/* Trip total summary */}
      {tripTotal > 0 && (
        <div className="trip-summary">
          <div>
            <div className="trip-total-label">Total accommodation</div>
            <div className="trip-total-val">{fmt(tripTotal)}</div>
          </div>
          <div className="trip-breakdown">
            {hotels.map(h => h.data?.price_total_aud && (
              <div key={h.name} className="trip-item">
                {h.name}: <span>{fmt(h.data.price_total_aud)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="cards-3">
        {hotels.map(({ name, idx, data, color }) => (
          <div key={name} className={`card c${idx}`}>
            <div className="card-accent" />
            <div className="card-label">{data?.location || name}</div>
            <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <div className="card-price">{fmt(data?.price_per_night_aud)}</div>
              <span className="card-price-unit">/ night</span>
            </div>
            <div className="card-dates">{data?.checkin ? `${data.checkin} → ${data.checkout}` : "—"}</div>
            <div className="card-divider" />
            <div className="meta-grid">
              <div><div className="meta-key">Hotel</div><div className="meta-val">{name}</div></div>
              <div><div className="meta-key">Nights</div><div className="meta-val">{data?.nights || "—"}</div></div>
              <div><div className="meta-key">Total</div><div className="meta-val">{fmt(data?.price_total_aud)}</div></div>
              <div><div className="meta-key">Rating</div><div className="meta-val">{data?.rating ? `${data.rating} ★` : "—"}</div></div>
            </div>
            {data?.booking_url && (
              <a className="book-btn" href={data.booking_url} target="_blank" rel="noopener">View on Booking →</a>
            )}
          </div>
        ))}
      </div>

      {chartData.length > 1 && (
        <div className="section">
          <div className="section-header">
            <div className="section-title">Price History</div>
            <div className="legend">
              {HOTEL_NAMES.map((n, i) => (
                <div key={n} className="legend-item">
                  <div className="legend-dot" style={{background: HOTEL_COLORS[i]}} />{n}
                </div>
              ))}
            </div>
          </div>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={chartData} margin={{ top: 5, right: 8, left: -8, bottom: 0 }}>
              <CartesianGrid stroke="#2a2a35" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: "#55556a", fontSize: 10, fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: "#55556a", fontSize: 10, fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} tickFormatter={v => `$${v}`} width={55} />
              <Tooltip content={<TooltipBox />} />
              {HOTEL_NAMES.map((n, i) => (
                <Line key={n} type="monotone" dataKey={n} stroke={HOTEL_COLORS[i]} strokeWidth={2} dot={{ r: 3, fill: HOTEL_COLORS[i], strokeWidth: 0 }} activeDot={{ r: 5 }} connectNulls />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="section">
        <div className="section-header"><div className="section-title">History Log</div></div>
        <div className="table-wrap">
          <table>
            <thead><tr>
              <th>Date</th><th>Hotel</th><th>Check-in</th><th>Check-out</th><th>Nights</th><th>Per Night</th><th>Total</th><th>Rating</th><th>Book</th>
            </tr></thead>
            <tbody>
              {rows.map((r, i) => {
                const hi = HOTEL_NAMES.indexOf(r.hotel);
                return (
                  <tr key={i}>
                    <td className="mono">{r.timestamp?.slice(0,10)}</td>
                    <td><span className={`badge h${hi >= 0 ? hi : 0}`}>{r.hotel}</span></td>
                    <td className="mono">{r.checkin}</td>
                    <td className="mono">{r.checkout}</td>
                    <td className="mono" style={{textAlign:"center"}}>{r.nights}</td>
                    <td className="price-cell">{fmt(r.price_per_night_aud)}</td>
                    <td className="price-cell">{fmt(r.price_total_aud)}</td>
                    <td className="mono">{r.rating ? `${r.rating} ★` : "—"}</td>
                    <td>{r.booking_url && <a className="tbl-link" href={r.booking_url} target="_blank" rel="noopener">Booking ↗</a>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab]           = useState("flights");
  const [flightRows, setFlights] = useState([]);
  const [hotelRows, setHotels]   = useState([]);
  const [loading, setLoading]    = useState(true);
  const [lastDate, setLastDate]  = useState(null);

  useEffect(() => {
    let done = 0;
    const finish = () => { done++; if (done === 2) setLoading(false); };

    Papa.parse(FLIGHT_CSV, {
      download: true, header: true, skipEmptyLines: true,
      complete: ({ data }) => { setFlights(data.reverse()); setLastDate(data[0]?.timestamp?.slice(0,10)); finish(); },
      error: finish,
    });
    Papa.parse(HOTEL_CSV, {
      download: true, header: true, skipEmptyLines: true,
      complete: ({ data }) => { setHotels(data.reverse()); finish(); },
      error: finish,
    });
  }, []);

  return (
    <>
      <style>{css}</style>
      <div className="app">
        <div className="header">
          <div className="eyebrow">Bali Trip Tracker · Ashley</div>
          <h1 className="title">ADL <span className="arrow">→</span> BALI</h1>
          <div className="subtitle">Flights + Hotels · Apr–May 2027 · Updated daily 08:30 ACST</div>
        </div>

        <div className="tabs">
          <button className={`tab ${tab === "flights" ? "active" : ""}`} onClick={() => setTab("flights")}>✈ Flights</button>
          <button className={`tab ${tab === "hotels" ? "active" : ""}`} onClick={() => setTab("hotels")}>🏨 Hotels</button>
        </div>

        {loading && <div className="loading">Loading...</div>}

        {!loading && tab === "flights" && (
          flightRows.length === 0
            ? <div className="empty">No flight data yet — run the tracker first.</div>
            : <FlightsTab rows={flightRows} />
        )}

        {!loading && tab === "hotels" && (
          hotelRows.length === 0
            ? <div className="empty">No hotel data yet — run the hotel tracker first.</div>
            : <HotelsTab rows={hotelRows} />
        )}

        {!loading && (
          <div className="footer">
            <span className="status-dot" />
            <span>Last tracked {lastDate || "—"} · Prices approximate, verify before booking</span>
          </div>
        )}
      </div>
    </>
  );
}
