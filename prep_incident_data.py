"""
prep_incident_data.py
Processes PHMSA hazardous liquid incident files and outputs JSON for visualizations.
Uses complete years 2002-2024 only.
"""
import csv
import json
from collections import defaultdict

GALLONS_PER_BARREL = 42.0

# ── Cause normalization ────────────────────────────────────────────────────────
CAUSE_MAP_09 = {
    'CORROSION':                    'Corrosion',
    'EQUIPMENT':                    'Equipment failure',
    'MATERIAL AND/OR WELD FAILURES':'Material/weld failure',
    'INCORRECT OPERATION':          'Incorrect operation',
    'EXCAVATION DAMAGE':            'Excavation damage',
    'NATURAL FORCES':               'Natural forces',
    'OTHER OUTSIDE FORCE DAMAGE':   'Outside force / other',
    'OTHER':                        'Outside force / other',
}
CAUSE_MAP_10 = {
    'CORROSION FAILURE':              'Corrosion',
    'EQUIPMENT FAILURE':              'Equipment failure',
    'MATERIAL FAILURE OF PIPE OR WELD':'Material/weld failure',
    'INCORRECT OPERATION':            'Incorrect operation',
    'EXCAVATION DAMAGE':              'Excavation damage',
    'NATURAL FORCE DAMAGE':           'Natural forces',
    'OTHER OUTSIDE FORCE DAMAGE':     'Outside force / other',
    'OTHER ACCIDENT CAUSE':           'Outside force / other',
}
ALL_CAUSES = ['Corrosion','Equipment failure','Incorrect operation',
              'Material/weld failure','Excavation damage','Natural forces',
              'Outside force / other']

# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_float(s, default=0.0):
    try:
        return float(str(s).strip())
    except (ValueError, TypeError):
        return default

# ── Load 2002-2009 ─────────────────────────────────────────────────────────────
print("Loading 2002-2009 file...")
with open(r'c:\Project Clean\PHSMA\accident_hazardous_liquid_jan2002_dec2009.txt',
          encoding='utf-8', errors='replace') as f:
    reader09 = list(csv.DictReader(f, delimiter='\t'))

rows_02_09 = []
for r in reader09:
    yr = r.get('IYEAR','').strip()
    if not yr.isdigit() or not (2002 <= int(yr) <= 2009):
        continue
    loss_raw = safe_float(r.get('LOSS', 0))
    recov_raw = safe_float(r.get('RECOV', 0))
    unit = r.get('SPUNIT_TXT','').strip().upper()
    if unit == 'GALLONS':
        loss_bbls  = loss_raw / GALLONS_PER_BARREL
        recov_bbls = recov_raw / GALLONS_PER_BARREL
    elif unit == 'BARRELS':
        loss_bbls  = loss_raw
        recov_bbls = recov_raw
    else:
        loss_bbls  = 0.0
        recov_bbls = 0.0
    cause_raw = r.get('GEN_CAUSE_TXT','').strip()
    rows_02_09.append({
        'year':  int(yr),
        'name':  r.get('NAME','').strip(),
        'cause': CAUSE_MAP_09.get(cause_raw, 'Outside force / other'),
        'released': loss_bbls,
        'recovered': recov_bbls,
        'state': r.get('ACSTATE','').strip(),
    })
print(f"  Loaded {len(rows_02_09)} rows (2002-2009)")

# ── Load 2010-present, filter to complete years 2010-2024 ─────────────────────
print("Loading 2010-present file...")
with open(r'c:\Project Clean\PHSMA\accident_hazardous_liquid_jan2010_present.txt',
          encoding='utf-8', errors='replace') as f:
    reader10 = list(csv.DictReader(f, delimiter='\t'))

rows_10_24 = []
for r in reader10:
    yr = r.get('IYEAR','').strip()
    if not yr.isdigit() or not (2010 <= int(yr) <= 2024):
        continue
    cause_raw = r.get('CAUSE','').strip()
    rows_10_24.append({
        'year':  int(yr),
        'name':  r.get('NAME','').strip(),
        'cause': CAUSE_MAP_10.get(cause_raw, 'Outside force / other'),
        'released': safe_float(r.get('UNINTENTIONAL_RELEASE_BBLS', 0)),
        'recovered': safe_float(r.get('RECOVERED_BBLS', 0)),
        'state': r.get('ONSHORE_STATE_ABBREVIATION','').strip(),
    })
print(f"  Loaded {len(rows_10_24)} rows (2010-2024)")

all_rows = rows_02_09 + rows_10_24
print(f"  Total combined: {len(all_rows)} rows")

# ══════════════════════════════════════════════════════════════════════════════
# 1. INCIDENTS PER YEAR + CAUSE BREAKDOWN
# ══════════════════════════════════════════════════════════════════════════════
year_counts      = defaultdict(int)
year_cause_counts = defaultdict(lambda: defaultdict(int))

for r in all_rows:
    year_counts[r['year']] += 1
    year_cause_counts[r['year']][r['cause']] += 1

years_sorted = sorted(year_counts.keys())
print("\n── Incidents per year ──────────────────────────────────────────────────")
print(f"{'Year':>6}  {'Total':>6}  {'Corrosion':>10}  {'EquipFail':>9}  {'IncorrOp':>9}  {'MatWeld':>8}  {'Excavation':>10}  {'NatForce':>9}  {'Other':>7}")
annual_totals = []
for yr in years_sorted:
    t = year_counts[yr]
    c = year_cause_counts[yr]
    row = {
        'year':  yr,
        'total': t,
        'causes': {k: c[k] for k in ALL_CAUSES}
    }
    annual_totals.append(row)
    print(f"  {yr}  {t:5d}  {c['Corrosion']:10d}  {c['Equipment failure']:9d}  "
          f"{c['Incorrect operation']:9d}  {c['Material/weld failure']:8d}  "
          f"{c['Excavation damage']:10d}  {c['Natural forces']:9d}  "
          f"{c['Outside force / other']:7d}")

total_2002_2024 = sum(year_counts.values())
total_2010_2024 = sum(v for k,v in year_counts.items() if k >= 2010)
total_corrosion_2010_2024 = sum(year_cause_counts[yr]['Corrosion'] for yr in years_sorted if yr >= 2010)
corr_pct = total_corrosion_2010_2024 / total_2010_2024 * 100 if total_2010_2024 else 0
print(f"\nTotal 2002-2024: {total_2002_2024}")
print(f"Total 2010-2024: {total_2010_2024}")
print(f"Corrosion 2010-2024: {total_corrosion_2010_2024} ({corr_pct:.1f}% of 2010-2024 incidents)")

# ══════════════════════════════════════════════════════════════════════════════
# 2. TOP 15 OPERATORS BY GROSS RELEASE 2010-2024
# ══════════════════════════════════════════════════════════════════════════════
print("\n── Top operators (2010-2024) by gross barrels released ─────────────────")
op_totals   = defaultdict(lambda: {'released': 0.0, 'recovered': 0.0, 'count': 0,
                                    'worst_bbls': 0.0, 'worst_year': '', 'worst_state': ''})
for r in rows_10_24:
    nm = r['name']
    op_totals[nm]['released']  += r['released']
    op_totals[nm]['recovered'] += r['recovered']
    op_totals[nm]['count']     += 1
    if r['released'] > op_totals[nm]['worst_bbls']:
        op_totals[nm]['worst_bbls']  = r['released']
        op_totals[nm]['worst_year']  = r['year']
        op_totals[nm]['worst_state'] = r['state']

top15 = sorted(op_totals.items(), key=lambda x: x[1]['released'], reverse=True)[:15]

print(f"\n{'#':>2}  {'Operator':<55}  {'Gross Rel':>10}  {'Recovered':>10}  {'Net Unrec':>10}  {'Count':>5}")
operator_data = []
for i, (name, d) in enumerate(top15):
    net = d['released'] - d['recovered']
    print(f"  {i+1:2d}  {name:<55}  {d['released']:10.0f}  {d['recovered']:10.0f}  "
          f"{net:10.0f}  {d['count']:5d}")
    operator_data.append({
        'name':        name,
        'released':    round(d['released'], 0),
        'recovered':   round(d['recovered'], 0),
        'net':         round(net, 0),
        'count':       d['count'],
        'worst_bbls':  round(d['worst_bbls'], 0),
        'worst_year':  d['worst_year'],
        'worst_state': d['worst_state'],
    })

# ── Potential merger/rebrand flags ────────────────────────────────────────────
print("\n── Merger/rebrand flags ─────────────────────────────────────────────────")
all_op_names = list(op_totals.keys())
# Check for common parent company keywords in top15
top15_names = [x[0] for x in top15]
keywords = ['ENTERPRISE','MAGELLAN','PLAINS','SUNOCO','KINDER MORGAN','COLONIAL',
            'ENBRIDGE','ENERGY TRANSFER','BUCKEYE','MARATHON','PHILLIPS','SHELL',
            'EXXON','CHEVRON','BP','HOLLY','EXPLORER','NUSTAR','ONEOK']
flags = []
for kw in keywords:
    matches = [nm for nm in all_op_names if kw in nm.upper()]
    if len(matches) > 1:
        in_top15 = [nm for nm in matches if nm in top15_names]
        if in_top15:
            total_rel = sum(op_totals[nm]['released'] for nm in matches)
            flags.append({'keyword': kw, 'names': matches, 'in_top15': in_top15, 'combined_released': total_rel})
            print(f"  [{kw}]: {len(matches)} entities total, in top15: {in_top15}")
            for nm in matches:
                print(f"      {op_totals[nm]['released']:8.0f} bbls  {nm}")

# ══════════════════════════════════════════════════════════════════════════════
# 3. AGE PROFILE CHECK: do top operators' pipes skew old?
# ══════════════════════════════════════════════════════════════════════════════
print("\n── Age profile check (Part I 2024) ──────────────────────────────────────")
# Columns for pre-EPA decades in Part I
PRE_EPA_COLS = ['PARTIPRE20','PARTI192029','PARTI193039','PARTI194049','PARTI195059','PARTI196069']
TOTAL_COL    = 'PARTITOTAL'
with open(r'c:\Project Clean\PHSMA\HL AR 2024 Part I.csv', encoding='utf-8', errors='replace') as f:
    parti_rows = list(csv.DictReader(f))

# Aggregate Part I by operator NAME (PARTA2NAMEOFCOMP) 
parti_by_name = defaultdict(lambda: {'pre_epa': 0.0, 'total': 0.0})
for r in parti_rows:
    nm = r.get('PARTA2NAMEOFCOMP','').strip()
    if not nm:
        continue
    pre = sum(safe_float(r.get(c, 0)) for c in PRE_EPA_COLS)
    tot = safe_float(r.get(TOTAL_COL, 0))
    parti_by_name[nm]['pre_epa'] += pre
    parti_by_name[nm]['total']   += tot

# For each top-15 incident operator, find the best name match in Part I
print(f"\n{'Incident operator':<55}  {'Part I match':<45}  {'Pre-EPA%':>9}  {'Pre-EPA mi':>10}")
age_results = []
for name, d in top15:
    # Exact match first
    if name in parti_by_name and parti_by_name[name]['total'] > 0:
        match = name
    else:
        # Fuzzy: pick best partial match by word overlap
        inc_words = set(name.upper().split())
        best_score, best_match = 0, None
        for pn in parti_by_name:
            pn_words = set(pn.upper().split())
            score = len(inc_words & pn_words)
            if score > best_score:
                best_score, best_match = score, pn
        match = best_match if best_score >= 2 else None

    if match:
        pre = parti_by_name[match]['pre_epa']
        tot = parti_by_name[match]['total']
        pct = pre / tot * 100 if tot else 0
        print(f"  {name:<55}  {match:<45}  {pct:8.1f}%  {pre:10.0f}")
        age_results.append({'operator': name, 'pre_epa_pct': round(pct,1), 'pre_epa_mi': round(pre,0)})
    else:
        print(f"  {name:<55}  {'NO MATCH':<45}  {'--':>9}  {'--':>10}")
        age_results.append({'operator': name, 'pre_epa_pct': None, 'pre_epa_mi': None})

national_pre_epa_pct = 88058 / 228514 * 100
print(f"\nNational average pre-EPA share: {national_pre_epa_pct:.1f}%")
print("Operators above national average skew older than the network median.")

# ══════════════════════════════════════════════════════════════════════════════
# 4. WRITE JSON OUTPUT
# ══════════════════════════════════════════════════════════════════════════════
import os
os.makedirs(r'c:\Project Clean\PHSMA\data', exist_ok=True)

with open(r'c:\Project Clean\PHSMA\data\incidents_by_year.json', 'w') as f:
    json.dump(annual_totals, f, indent=2)

with open(r'c:\Project Clean\PHSMA\data\top_operators.json', 'w') as f:
    json.dump(operator_data, f, indent=2)

print("\n── Done ─────────────────────────────────────────────────────────────────")
print("Wrote data/incidents_by_year.json")
print("Wrote data/top_operators.json")
