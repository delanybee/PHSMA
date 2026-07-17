"""
Run all pipeline visualizations and save as standalone HTML files.
Open the HTML files in any browser to see the interactive charts.
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import xlrd
import warnings, os
warnings.filterwarnings('ignore')

BASE   = r'c:\Project Clean\PHSMA'
OUT    = rf'{BASE}\visuals'
os.makedirs(OUT, exist_ok=True)

# ── 1. Load mileage summary ─────────────────────────────────────────────────
wb = xlrd.open_workbook(rf'{BASE}\Mileage Summary\Extracted\haz_liquid_annual_stat.xls')
ws = wb.sheet_by_index(0)

rows = []
for r in range(ws.nrows):
    vals = [ws.cell_value(r, c) for c in range(ws.ncols)]
    if vals[1] and str(vals[1]).replace('.0','').isdigit():
        rows.append({
            'year':   int(vals[1]),
            'total':  vals[3],
            'rpp':    vals[4],
            'hvl':    vals[5],
            'crude':  vals[6],
            'co2':    vals[7],
            'ethanol':vals[8] if vals[8] else 0,
        })

miles = pd.DataFrame(rows)
total_2025 = float(miles[miles.year == 2025]['total'].values[0])
print(f"Mileage data loaded: {miles.year.min()}–{miles.year.max()}")

# ── 2. Event annotations ────────────────────────────────────────────────────
events = [
    (2008, "Shale boom begins",                  "top",
     "Hydraulic fracturing unlocks vast Bakken and Permian Basin reserves. "
     "The US crude network will nearly double over the next decade."),
    (2010, "Kalamazoo River spill — $1.2B cleanup", "bottom",
     "Enbridge Line 6B ruptures near Marshall, Michigan. ~20,000 barrels of "
     "diluted bitumen into the Kalamazoo River — largest inland spill in US Midwest history. "
     "Pipeline was 41 years old. River closed two years."),
    (2015, "Refugio spill — $92M cleanup",        "bottom",
     "50-year-old Plains All American pipeline ruptures near Santa Barbara. Corrosion. "
     "100,000+ gallons reach Pacific Ocean. Company initially failed to report it. "
     "$60M+ in penalties."),
    (2017, "Dakota Access opens — $3.8B",         "top",
     "1,172-mile DAPL becomes operational after Standing Rock protests drew global attention. "
     "Crosses under Lake Oahe, the tribe's water source. 750,000 bbl/day of Bakken crude."),
    (2019, "Crude network peaks",                  "top",
     "Crude oil pipeline mileage peaks at 84,475 miles — a 71% increase from 2004. "
     "Permian Basin boom accounts for nearly half of US crude production."),
    (2021, "Colonial ransomware — $4.4M ransom",   "bottom",
     "Cyberattack shuts down the Colonial Pipeline for 6 days. 45% of East Coast fuel supply. "
     "Gas shortages Georgia to New Jersey. DarkSide extorted $4.4M; FBI recovered $2.3M."),
    (2021, "Network peaks: 230,036 mi",            "top",
     "US hazardous liquid pipeline network reaches all-time high: 230,036 miles. "
     "That's 9.2× Earth's circumference — enough to reach the Moon and back."),
    (2024, "Sable pipeline restarts",              "bottom",
     "Nearly a decade after Refugio spill, Sable Offshore wins approval to restart the "
     "same California coastal infrastructure. Fiercely contested. Pipe not replaced — only inspected."),
]

event_types = {
    "Kalamazoo River spill — $1.2B cleanup":  'spill',
    "Refugio spill — $92M cleanup":           'spill',
    "Colonial ransomware — $4.4M ransom":     'spill',
    "Sable pipeline restarts":                'policy',
    "Dakota Access opens — $3.8B":            'open',
    "Shale boom begins":                      'trend',
    "Crude network peaks":                    'trend',
    "Network peaks: 230,036 mi":              'trend',
}

COLOR = {
    'crude':  '#D4380D',
    'rpp':    '#1677FF',
    'hvl':    '#389E0D',
    'co2':    '#722ED1',
    'ethanol':'#FA8C16',
    'total':  '#262626',
    'spill':  '#CF1322',
    'open':   '#0958D9',
    'trend':  '#389E0D',
    'policy': '#722ED1',
}

# ── 3. VISUAL 1A — Annotated growth line chart ──────────────────────────────
fig1 = go.Figure()

for key, label, dash, width in [
    ('crude',   'Crude Oil',                         'solid', 2.5),
    ('rpp',     'Refined Products (gas/diesel/jet)',  'solid', 2.5),
    ('hvl',     'Highly Volatile Liquids (propane/butane)', 'solid', 2),
    ('co2',     'CO₂ & Other',                       'dot',   1.5),
    ('ethanol', 'Fuel Ethanol',                      'dot',   1.5),
]:
    fig1.add_trace(go.Scatter(
        x=miles['year'], y=miles[key], name=label,
        line=dict(color=COLOR[key], dash=dash, width=width),
        hovertemplate=f'<b>{label}</b><br>%{{x}}: %{{y:,.0f}} miles<extra></extra>',
    ))

fig1.add_trace(go.Scatter(
    x=miles['year'], y=miles['total'], name='Total Network',
    line=dict(color=COLOR['total'], width=3.5),
    hovertemplate='<b>Total Network</b><br>%{x}: %{y:,.0f} miles<extra></extra>',
))

for year, label, side, blurb in events:
    row = miles[miles.year == year]
    if row.empty:
        continue
    y_val    = float(row['total'].values[0])
    etype    = event_types.get(label, 'trend')
    color    = COLOR[etype]
    y_offset = 9000 if side == 'top' else -9000
    ay_off   = 45   if side == 'top' else -45

    fig1.add_vline(x=year, line_width=1, line_dash='dash',
                   line_color=color, opacity=0.4)
    fig1.add_annotation(
        x=year, y=y_val + y_offset,
        text=f'<b>{label}</b>',
        showarrow=True, arrowhead=2, arrowsize=1,
        arrowwidth=1.5, arrowcolor=color,
        ax=0, ay=ay_off,
        font=dict(size=10, color=color),
        bgcolor='rgba(255,255,255,0.9)',
        bordercolor=color, borderwidth=1, borderpad=3,
        hovertext=blurb,
    )

fig1.update_layout(
    title=dict(
        text='<b>The Invisible Network: U.S. Hazardous Liquid Pipeline Miles, 2004–2025</b><br>'
             '<sup>Source: PHMSA Annual Report Mileage Summary (Form 7000-1.1) · Hover annotations for details</sup>',
        font=dict(size=16), x=0.5, xanchor='center'
    ),
    xaxis=dict(title='Year', tickmode='linear', dtick=2, gridcolor='#f0f0f0'),
    yaxis=dict(title='Pipeline Miles', tickformat=',', gridcolor='#f0f0f0'),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
    hovermode='x unified',
    plot_bgcolor='white', paper_bgcolor='white',
    width=1200, height=680,
    margin=dict(l=70, r=50, t=130, b=70),
)

out1 = rf'{OUT}\visual_1a_growth_chart.html'
fig1.write_html(out1, include_plotlyjs='cdn')
print(f"Saved: {out1}")

# ── 4. VISUAL 1C — Scale comparison bar ─────────────────────────────────────
EARTH = 24_901
INTERSTATE = 48_786

fig_scale = go.Figure(go.Bar(
    x=[total_2025, INTERSTATE, EARTH * 9.13],
    y=['US Hazardous Liquid Pipelines (2025)',
       'US Interstate Highway System',
       '9× Earth\'s circumference (for scale)'],
    orientation='h',
    marker_color=['#D4380D', '#1677FF', '#8c8c8c'],
    text=[f'{total_2025:,.0f} mi', f'{INTERSTATE:,.0f} mi', f'{EARTH*9.13:,.0f} mi'],
    textposition='outside',
    hovertemplate='%{y}: %{x:,.0f} miles<extra></extra>',
))
fig_scale.update_layout(
    title=dict(text='<b>How Big Is 227,000 Miles?</b>',
               font=dict(size=15), x=0.5, xanchor='center'),
    xaxis=dict(title='Miles', tickformat=',', gridcolor='#f0f0f0'),
    yaxis=dict(autorange='reversed'),
    plot_bgcolor='white', paper_bgcolor='white',
    width=860, height=300,
    margin=dict(l=270, r=110, t=70, b=50),
    showlegend=False,
)
out_scale = rf'{OUT}\visual_1c_scale_callout.html'
fig_scale.write_html(out_scale, include_plotlyjs='cdn')
print(f"Saved: {out_scale}")

# ── 5. Load Part I decade data ──────────────────────────────────────────────
decade_cols = [
    'PARTIUNKWN', 'PARTIPRE20',
    'PARTI192029', 'PARTI193039', 'PARTI194049',
    'PARTI195059', 'PARTI196069', 'PARTI197079',
    'PARTI198089', 'PARTI199099',
    'PARTI200009', 'PARTI201019', 'PARTI202029'
]
decade_labels = {
    'PARTIUNKWN':  'Unknown',   'PARTIPRE20':  'Pre-1920',
    'PARTI192029': '1920s',     'PARTI193039': '1930s',
    'PARTI194049': '1940s',     'PARTI195059': '1950s',
    'PARTI196069': '1960s',     'PARTI197079': '1970s',
    'PARTI198089': '1980s',     'PARTI199099': '1990s',
    'PARTI200009': '2000s',     'PARTI201019': '2010s',
    'PARTI202029': '2020s',
}
frames = []
for year in range(2017, 2026):
    df = pd.read_csv(rf'{BASE}\HL AR {year} Part I.csv')
    for c in decade_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
    totals = df[decade_cols].sum().to_dict()
    totals['year'] = year
    frames.append(totals)

decade_df = pd.DataFrame(frames).set_index('year').rename(columns=decade_labels)

ordered = ['Pre-1920','1920s','1930s','1940s','1950s','1960s',
           '1970s','1980s','1990s','2000s','2010s','2020s']
snap = decade_df.loc[2025].drop('Unknown', errors='ignore')
total_snap = snap.sum()

pre_1970 = sum(snap.get(d, 0) for d in ['Pre-1920','1920s','1930s','1940s','1950s','1960s'])
pre_1980 = pre_1970 + sum(snap.get(d, 0) for d in ['1970s','1980s'])

print(f"Part I loaded · Pre-1970: {pre_1970:,.0f} mi ({pre_1970/total_snap*100:.0f}%)")

# ── 6. VISUAL 3A — Timeline strip ──────────────────────────────────────────
decade_colors = {
    'Pre-1920':'#7F1D1D','1920s':'#991B1B','1930s':'#B91C1C','1940s':'#DC2626',
    '1950s':'#F97316','1960s':'#FB923C',
    '1970s':'#FCD34D','1980s':'#86EFAC',
    '1990s':'#4ADE80','2000s':'#22C55E','2010s':'#16A34A','2020s':'#166534',
}
decade_age = {
    'Pre-1920':'100+ years','1920s':'95–105 yrs','1930s':'85–95 yrs',
    '1940s':'75–85 yrs','1950s':'65–75 yrs','1960s':'55–65 yrs',
    '1970s':'45–55 yrs','1980s':'35–45 yrs','1990s':'25–35 yrs',
    '2000s':'15–25 yrs','2010s':'5–15 yrs','2020s':'Under 5 yrs',
}
decade_context = {
    'Pre-1920':'No federal pipeline safety law','1920s':'No federal pipeline safety law',
    '1930s':'Great Depression','1940s':'WWII era',
    '1950s':'Eisenhower / Post-war boom','1960s':'Apollo program era',
    '1970s':'OPEC oil crisis · safety law just passed (1968)',
    '1980s':'Hazardous Liquid Pipeline Safety Act (1979)',
    '1990s':'Post-Exxon Valdez reforms','2000s':'Pipeline Safety Improvement Act (2002)',
    '2010s':'Post-Kalamazoo reforms · PIPES Act (2016)',
    '2020s':'PIPES Act (2020) · energy transition',
}

fig_strip = go.Figure()
x_cursor = 0
for dec in ordered:
    mi  = snap.get(dec, 0)
    pct = mi / total_snap * 100
    clr = decade_colors.get(dec, '#888')
    hover = (f"<b>{dec}</b><br>{mi:,.0f} miles ({pct:.1f}%)<br>"
             f"{decade_age.get(dec,'')} in 2025<br>"
             f"<i>{decade_context.get(dec,'')}</i>")
    fig_strip.add_trace(go.Bar(
        x=[mi], y=['Pipeline'], orientation='h', base=x_cursor,
        marker_color=clr, marker_line=dict(color='white', width=1),
        name=dec,
        hovertemplate=hover + '<extra></extra>',
        text=dec if pct > 2.5 else '',
        textposition='inside', textfont=dict(color='white', size=10),
    ))
    x_cursor += mi

for thr, lbl, clr in [
    (pre_1970, f'Pre-1970: {pre_1970:,.0f} mi ({pre_1970/total_snap*100:.0f}%)', '#B91C1C'),
    (pre_1980, f'Pre-1980: {pre_1980:,.0f} mi ({pre_1980/total_snap*100:.0f}%)', '#F97316'),
]:
    fig_strip.add_vline(x=thr, line_width=2, line_dash='dash', line_color=clr,
                        annotation_text=f'<b>{lbl}</b>',
                        annotation_position='top',
                        annotation_font=dict(color=clr, size=10))

fig_strip.update_layout(
    title=dict(
        text='<b>When Was It Built? U.S. Hazardous Liquid Pipeline — Mileage by Installation Decade (2025)</b><br>'
             '<sup>Segment width = miles of active pipe installed in that decade · Hover for historical context</sup>',
        font=dict(size=14), x=0.5, xanchor='center'
    ),
    xaxis=dict(title='Cumulative Miles', tickformat=',', gridcolor='#f0f0f0'),
    yaxis=dict(visible=False),
    barmode='stack', plot_bgcolor='white', paper_bgcolor='white',
    width=1200, height=310,
    margin=dict(l=40, r=40, t=110, b=120),
    legend=dict(orientation='h', yanchor='top', y=-0.15,
                xanchor='center', x=0.5, font=dict(size=9)),
)
out_strip = rf'{OUT}\visual_3a_timeline_strip.html'
fig_strip.write_html(out_strip, include_plotlyjs='cdn')
print(f"Saved: {out_strip}")

# ── 7. VISUAL 3C — Age tier donut ──────────────────────────────────────────
tier_map = {
    'Pre-1920':'Pre-1970 (55+ yrs)','1920s':'Pre-1970 (55+ yrs)',
    '1930s':'Pre-1970 (55+ yrs)','1940s':'Pre-1970 (55+ yrs)',
    '1950s':'Pre-1970 (55+ yrs)','1960s':'Pre-1970 (55+ yrs)',
    '1970s':'1970–1989 (35–55 yrs)','1980s':'1970–1989 (35–55 yrs)',
    '1990s':'1990–2009 (15–35 yrs)','2000s':'1990–2009 (15–35 yrs)',
    '2010s':'Post-2010 (under 15 yrs)','2020s':'Post-2010 (under 15 yrs)',
}
tier_context = {
    'Pre-1970 (55+ yrs)':       'Before the EPA, Clean Water Act, or any federal hazardous liquid pipeline safety law',
    '1970–1989 (35–55 yrs)':    'Early regulatory era — basic federal oversight just beginning',
    '1990–2009 (15–35 yrs)':    'Post-Exxon Valdez reform era — modern standards taking shape',
    'Post-2010 (under 15 yrs)': 'Modern construction — shale boom pipeline surge',
}
tier_totals = {}
for dec, mi in snap.items():
    t = tier_map.get(dec)
    if t:
        tier_totals[t] = tier_totals.get(t, 0) + mi

tier_order  = ['Pre-1970 (55+ yrs)','1970–1989 (35–55 yrs)',
               '1990–2009 (15–35 yrs)','Post-2010 (under 15 yrs)']
tier_colors = ['#B91C1C','#F97316','#86EFAC','#166534']
vals = [tier_totals[t] for t in tier_order]
pcts = [v/total_snap*100 for v in vals]

fig_donut = go.Figure(go.Pie(
    labels=tier_order, values=vals, hole=0.55,
    marker_colors=tier_colors,
    customdata=[[tier_context[t], f'{v:,.0f} miles', f'{p:.1f}%']
                for t, v, p in zip(tier_order, vals, pcts)],
    hovertemplate=(
        '<b>%{label}</b><br>%{customdata[1]}  (%{customdata[2]})<br>'
        '<i>%{customdata[0]}</i><extra></extra>'
    ),
    textinfo='percent+label', textfont=dict(size=11),
))
fig_donut.update_layout(
    title=dict(
        text='<b>How Old Is the U.S. Hazardous Liquid Pipeline Network?</b><br>'
             f'<sup>{total_snap:,.0f} total miles — 2025 data · Hover for regulatory context</sup>',
        font=dict(size=14), x=0.5, xanchor='center'
    ),
    annotations=[dict(
        text=f'<b>{pre_1970/total_snap*100:.0f}%</b><br>predates<br>the EPA',
        x=0.5, y=0.5, font=dict(size=15, color='#B91C1C'), showarrow=False
    )],
    plot_bgcolor='white', paper_bgcolor='white',
    width=680, height=560,
    margin=dict(l=40, r=40, t=110, b=50),
    legend=dict(orientation='h', yanchor='bottom', y=-0.12, xanchor='center', x=0.5)
)
out_donut = rf'{OUT}\visual_3c_age_donut.html'
fig_donut.write_html(out_donut, include_plotlyjs='cdn')
print(f"Saved: {out_donut}")

# ── 8. BONUS — Pre-1970 trend 2017-2025 ─────────────────────────────────────
old_decs = ['Pre-1920','1920s','1930s','1940s','1950s','1960s']
old_rows = []
for yr in range(2017, 2026):
    row   = decade_df.loc[yr]
    old_mi = sum(row.get(d, 0) for d in old_decs)
    tot_mi = sum(row.get(d, 0) for d in ordered if d in row.index)
    old_rows.append({'year': yr, 'old_mi': old_mi, 'pct': old_mi/tot_mi*100 if tot_mi else 0})
old_df = pd.DataFrame(old_rows)

fig_trend = make_subplots(specs=[[{'secondary_y': True}]])
fig_trend.add_trace(
    go.Bar(x=old_df.year, y=old_df.old_mi, name='Pre-1970 miles',
           marker_color='#F97316', opacity=0.75,
           hovertemplate='%{x}: %{y:,.0f} miles<extra></extra>'),
    secondary_y=False)
fig_trend.add_trace(
    go.Scatter(x=old_df.year, y=old_df.pct, name='% of total network',
               line=dict(color='#B91C1C', width=2.5),
               mode='lines+markers',
               hovertemplate='%{x}: %{y:.1f}% of network<extra></extra>'),
    secondary_y=True)
fig_trend.update_layout(
    title=dict(
        text='<b>Pre-1970 Pipeline Miles Still in Active Service, 2017–2025</b><br>'
             '<sup>Is the oldest infrastructure being retired — or just growing as a share?</sup>',
        font=dict(size=13), x=0.5, xanchor='center'
    ),
    xaxis=dict(title='Year', tickmode='linear', dtick=1, gridcolor='#f0f0f0'),
    plot_bgcolor='white', paper_bgcolor='white',
    width=950, height=440, hovermode='x unified',
    margin=dict(l=70, r=90, t=110, b=70),
    legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='left', x=0),
)
fig_trend.update_yaxes(title_text='Miles of Pre-1970 Pipe', secondary_y=False,
                        tickformat=',', gridcolor='#f0f0f0')
fig_trend.update_yaxes(title_text='% of Total Network', secondary_y=True,
                        ticksuffix='%', showgrid=False)
out_trend = rf'{OUT}\visual_bonus_aging_trend.html'
fig_trend.write_html(out_trend, include_plotlyjs='cdn')
print(f"Saved: {out_trend}")

print("\n✓ All 4 visuals saved to:", OUT)
print("Open the HTML files in any browser to view interactive charts.")
