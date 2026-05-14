import pandas as pd

file = "alerts.xlsx"

df = pd.read_excel(file)

n = len(df)
for i in range(n):
    rank = n - i
    df.loc[i, "vendor"] = f"Vendor {rank}"
    df.loc[i, "vendor_id"] = f"V-{1000 + rank}"
    df.loc[i, "vendor_domain"] = f"vendor{rank}.com"

df.to_excel(file, index=False)

print("Done! Old data converted to Vendor format")