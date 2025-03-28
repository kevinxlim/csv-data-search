from flask import Flask, jsonify, render_template, send_from_directory
import pandas as pd
import numpy as np

app = Flask(__name__)

supplier_configs = {
    "Ingram Micro": {
        "file": "141421.csv",
        "brand": "Vendor Name",
        "description": "Ingram Part Description",
        "mfr_code": "Vendor Part Number",
        "cost": "Customer Price",
        "stock": "Available Quantity",
        "long_description": "Material Long Description"  # Added
    },
    "Dove": {
        "file": "dealerpricelist.csv",
        "brand": "Brand",
        "description": "Description",
        "mfr_code": "Mftr Code",
        "cost": "Price",
        "stock": "Qty",
        "long_description": "Long Description"  # Added
    },
    "Dicker Data": {
        "file": "DickerDataDataFeedCSV.csv",
        "brand": "Vendor",
        "description": "StockDescription",
        "mfr_code": "VendorStockCode",
        "cost": "DealerEx",
        "stock": "StockAvailable",
        "long_description": "PrimaryCategory"  # Added
    },
    "Computer Dynamics": {
        "file": "pricefile.csv",
        "brand": "Brand",
        "description": "Description",
        "mfr_code": "Manufacturer's Part Number",
        "cost": "Dealer",
        "stock": "Qty in stock - Total"
    },
    "SnapperNet": {
        "file": "snappernet2.csv",
        "brand": "Brand",
        "description": "Description",
        "mfr_code": "Product_Code",
        "cost": "Reseller_Buy",
        "stock": "Stock",
        "long_description": "Category"
    }
}

columns = ["Brand", "Description", "ManufacturerCode", "Cost", "SellPrice", "Stock", "Supplier", "LongDescription"]

def load_data():
    all_data = []
    for supplier, config in supplier_configs.items():
        try:
            df = pd.read_csv(config["file"], low_memory=False)
            print(f"{supplier} rows loaded: {len(df)}")
            
            # Rename columns, including the new long description if it exists
            rename_dict = {
                config["brand"]: "Brand",
                config["description"]: "Description",
                config["mfr_code"]: "ManufacturerCode",
                config["cost"]: "Cost",
                config["stock"]: "Stock"
            }
            if "long_description" in config:
                rename_dict[config["long_description"]] = "LongDescription"
            
            df = df.rename(columns=rename_dict)
            
            # Convert Cost and Stock to numeric, coercing errors to NaN
            df["Cost"] = df["Cost"].replace({r',': ''}, regex=True)
            df["Cost"] = pd.to_numeric(df["Cost"], errors="coerce")
            # df["Stock"] = pd.to_numeric(df["Stock"], errors="coerce")
            print(f"{supplier} after numeric conversion: {len(df)} rows")
            
            # Drop rows where Cost or Stock is NaN
            df = df.dropna(subset=["Cost", "Stock"])
            print(f"{supplier} after dropna: {len(df)} rows")
            
            # Filter stock values
            df = df[(df["Stock"] > 0) & (df["Stock"] < 999999999)]
            print(f"{supplier} after stock filter: {len(df)} rows")
            
            # Special handling for Ingram Micro to combine additional columns into LongDescription
            if supplier == "Ingram Micro":
                # Create a new LongDescription by combining existing long description with additional columns
                df["LongDescription"] = df["LongDescription"].fillna("")
                additional_columns = ["Product Family", "Category Description", "Sub-Category Description", "Category ID Description"]
                
                # Process each row individually
                for idx, row in df.iterrows():
                    additional_info = []
                    for col in additional_columns:
                        if col in df.columns and pd.notna(row[col]) and str(row[col]).strip():
                            additional_info.append("\n" + str(row[col]).strip())
                    if additional_info:
                        df.at[idx, "LongDescription"] = row["LongDescription"] + "\n" + "".join(additional_info)
            
            # Special handling for Dicker Data to combine additional columns into LongDescription
            if supplier == "Dicker Data":
                # Create a new LongDescription by combining existing long description with additional columns
                df["LongDescription"] = df["LongDescription"].fillna("")
                additional_columns = ["SecondaryCategory", "TertiaryCategory"]
                
                # Process each row individually
                for idx, row in df.iterrows():
                    additional_info = []
                    for col in additional_columns:
                        if col in df.columns and pd.notna(row[col]) and str(row[col]).strip():
                            additional_info.append("\n" + str(row[col]).strip())
                    if additional_info:
                        df.at[idx, "LongDescription"] = row["LongDescription"] + "".join(additional_info)
            
            # Calculate SellPrice
            df["SellPrice"] = df["Cost"] * 1.2
            df["Supplier"] = supplier
            
            # Ensure all columns are present, fill missing LongDescription with None
            for col in columns:
                if col not in df.columns:
                    df[col] = None
            df = df[columns]
            all_data.append(df)
        except Exception as e:
            print(f"Error processing {supplier}: {e}")
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.replace({np.nan: None})
        print("Total rows in final data:", len(combined_df))
        return combined_df.to_dict(orient="records")
    print("No data processed")
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    data = load_data()
    return jsonify(data)
    
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)