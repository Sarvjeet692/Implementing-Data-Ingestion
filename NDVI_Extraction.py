from sentinelsat import SentinelAPI
from datetime import datetime, timedelta
import rasterio
import numpy as np
import pandas as pd
from shapely.geometry import Point, box
import os

def get_ndvi_values():
    # Sentinel Hub credentials - you'll need to register at https://scihub.copernicus.eu/
    username = 'your_username'  # Replace with your username
    password = 'your_password'  # Replace with your password
    
    # Connect to Sentinel API
    api = SentinelAPI(username, password, 'https://scihub.copernicus.eu/dhus')
    
    # Define area of interest (Hooghly district)
    footprint = Point(88.39, 22.90).buffer(0.1)  # approximately 10km buffer
    
    # Search parameters
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 3, 1)
    
    # Query Sentinel-2 data
    products = api.query(
        footprint,
        date=(start_date, end_date),
        platformname='Sentinel-2',
        processinglevel='Level-2A',
        cloudcoverpercentage=(0, 20)
    )
    
    # Download and process data
    ndvi_values = []
    
    for product_id, product_info in products.items():
        # Download the product
        api.download(product_id)
        
        # Get the downloaded file path
        file_path = product_info['title'] + '.SAFE'
        
        # Process bands (B4 - Red, B8 - NIR)
        red_band = None
        nir_band = None
        
        for root, dirs, files in os.walk(file_path):
            for file in files:
                if file.endswith('B04_10m.jp2'):  # Red band
                    red_band = rasterio.open(os.path.join(root, file))
                elif file.endswith('B08_10m.jp2'):  # NIR band
                    nir_band = rasterio.open(os.path.join(root, file))
        
        if red_band is not None and nir_band is not None:
            # Read the bands as arrays
            red = red_band.read(1).astype(float)
            nir = nir_band.read(1).astype(float)
            
            # Calculate NDVI
            ndvi = (nir - red) / (nir + red)
            
            # Calculate mean NDVI for the region
            mean_ndvi = np.nanmean(ndvi)
            
            ndvi_values.append({
                'date': product_info['beginposition'].date(),
                'ndvi': mean_ndvi,
                'cloud_coverage': product_info['cloudcoverpercentage']
            })
            
            # Close the files
            red_band.close()
            nir_band.close()
        
        # Clean up downloaded files
        os.remove(file_path)
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(ndvi_values)
    df.to_csv('hooghly_ndvi_sentinel.csv', index=False)
    return df

if __name__ == "__main__":
    # Install required packages first:
    # pip install sentinelsat rasterio shapely pandas numpy
    
    print("Starting NDVI extraction...")
    try:
        ndvi_df = get_ndvi_values()
        print("\nNDVI values have been extracted and saved to 'hooghly_ndvi_sentinel.csv'")
        print("\nSummary statistics:")
        print(ndvi_df.describe())
    except Exception as e:
        print(f"An error occurred: {str(e)}")
