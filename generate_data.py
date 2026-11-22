from pathlib import Path
import pandas as pd
# The committed CSV files in ./data are the reproducible synthetic demo dataset.
# This script validates their presence and basic schema.
root = Path(__file__).parent / 'data'
for name in ['clients.csv','inbox_records.csv','support_tickets.csv','crm_notes.csv']:
    df = pd.read_csv(root / name)
    print(f'{name}: {len(df)} rows; columns={list(df.columns)}')
