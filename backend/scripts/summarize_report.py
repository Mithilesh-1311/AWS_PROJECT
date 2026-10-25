import json

with open('backend/artifacts/reports/dataset_inspection_report.json') as f:
    r = json.load(f)

# Print trial info for S1
s1 = r['subjects']['S1']
print('S1 trial_info:')
print(json.dumps(s1.get('trial_info'), indent=2))
print()

# Compare all subjects
for sid in sorted(r['subjects'].keys(), key=lambda x: int(x[1:])):
    s = r['subjects'][sid]
    ti = s.get('trial_info', {})
    segs = ti.get('segments_per_value', {})
    eog_s = s.get('eog_samples', '?')
    cs_vals = ti.get('unique_values', [])
    pd_val = s.get('pd_value', '?')
    dist_val = s.get('dist_screen_value', '?')
    print(f"{sid}: EOG={eog_s}, CS_vals={cs_vals}, segs={segs}, PD={pd_val}, Dist={dist_val}")
