"""
MeasurementQualifier Code-Description Pairing Analysis
Purpose: Extract and document the 1:1 mapping between codes and descriptions.

Since MeasurementQualifier has a direct 1:1 relationship with MeasurementQualifierDescription,
this script extracts the definitive code-description pairs for reference documentation.
"""

import pandas as pd

# Configuration
DATA_PATH = "data/raw/alberta_surface_water_quality_data.csv"
OUTPUT_DIR = "output/eda_outputs"

print("=" * 80)
print("MEASUREMENT QUALIFIER CODE-DESCRIPTION PAIRING")
print("=" * 80)

# Load data
print("\nLoading data...")
df = pd.read_csv(DATA_PATH, low_memory=False)
print(f"✓ Loaded {len(df):,} records\n")

# Extract unique code-description pairs with frequencies
print("Extracting code-description pairs...")
code_desc_pairs = (
    df.groupby(['MeasurementQualifier', 'MeasurementQualifierDescription'])
    .size()
    .reset_index(name='Frequency')
    .sort_values(['MeasurementQualifier', 'Frequency'], ascending=[True, False])
)

# Summary statistics
clean_data = len(df[df['MeasurementQualifier'].isna()])
flagged_data = len(df[df['MeasurementQualifier'].notna()])

print(f"✓ Total records: {len(df):,}")
print(f"  - Clean (no qualifier): {clean_data:,} ({clean_data/len(df)*100:.2f}%)")
print(f"  - Flagged (with qualifier): {flagged_data:,} ({flagged_data/len(df)*100:.2f}%)")
print(f"✓ Unique code-description pairs: {len(code_desc_pairs)}\n")

# Display and save pairs
print("Code-Description Mapping:")
print("=" * 100)
for _, row in code_desc_pairs.iterrows():
    code = row['MeasurementQualifier']
    desc = row['MeasurementQualifierDescription']
    freq = row['Frequency']
    pct = (freq / len(df)) * 100
    print(f"{str(code):12s} │ {str(desc):50s} │ {freq:6,d} ({pct:5.2f}%)")

print("=" * 100)

# Save to CSV
code_desc_pairs.to_csv(f"{OUTPUT_DIR}/qualifier_code_description_pairs.csv", index=False)
print(f"\n✓ Pairs saved to {OUTPUT_DIR}/qualifier_code_description_pairs.csv")

# Calculate data quality metrics by code
print("\n" + "=" * 80)
print("DATA QUALITY METRICS BY CODE")
print("=" * 80)

for code in sorted(df['MeasurementQualifier'].dropna().unique()):
    code_data = df[df['MeasurementQualifier'] == code]
    desc = code_data['MeasurementQualifierDescription'].iloc[0]
    
    print(f"\n{code}: {desc}")
    print(f"  Records: {len(code_data):,} ({len(code_data)/len(df)*100:.2f}%)")
    print(f"  Has MeasurementValue: {code_data['MeasurementValue'].notna().sum():,} ({code_data['MeasurementValue'].notna().sum()/len(code_data)*100:.1f}%)")
    print(f"  Has SampleComment: {code_data['SampleComment'].notna().sum():,}")
    print(f"  Has MeasurementComment: {code_data['MeasurementComment'].notna().sum():,}")
    print(f"  Has MeasurementFlag: {code_data['MeasurementFlag'].notna().sum():,}")

print("\n✓ Analysis complete!")
