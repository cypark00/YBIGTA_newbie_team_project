from fastapi import APIRouter, HTTPException, Depends, status
from typing import Any, Dict, List, Union
import pandas as pd
import tempfile
import os
from contextlib import contextmanager

from database.mongodb_connection import mongo_db
from app.responses.base_response import BaseResponse
from review_analysis.preprocessing.kakaomap_processor import KakaoMapProcessor
from review_analysis.preprocessing.myrealtrip_processor import MyRealTripProcessor
from review_analysis.preprocessing.tripdotcom_processor import TripDotComProcessor

review = APIRouter(prefix="/api/review")

# Supported site processors mapping
SITE_PROCESSORS = {
    "kakaomap": KakaoMapProcessor,
    "myrealtrip": MyRealTripProcessor,
    "tripdotcom": TripDotComProcessor,
}

@contextmanager
def temporary_files(*suffixes):
    """Context manager for handling temporary files with automatic cleanup."""
    temp_files = []
    try:
        for suffix in suffixes:
            if suffix.endswith('.csv'):
                # For CSV files, create with text mode and encoding
                temp_file = tempfile.NamedTemporaryFile(
                    mode="w+",
                    suffix=suffix, 
                    delete=False, 
                    encoding="utf-8"
                )
            else:
                # For other files, create in binary mode without encoding
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=suffix, 
                    delete=False
                )
            temp_files.append(temp_file.name)
            temp_file.close()  # Close file handle but keep the file
        yield temp_files
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except OSError:
                pass

def validate_site_name(site_name: str) -> str:
    """Validate and normalize site name."""
    if site_name not in SITE_PROCESSORS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown site_name: {site_name}. Supported sites: {list(SITE_PROCESSORS.keys())}"
        )
    return site_name

def fetch_review_data(collection_name: str) -> pd.DataFrame:
    """Fetch review data from MongoDB and convert to DataFrame."""
    try:
        collection = mongo_db[collection_name]
        db_data = list(collection.find({}))
        
        if not db_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No data found in collection: {collection_name}"
            )
        
        df = pd.DataFrame(db_data)
        # Remove MongoDB's _id field if present
        if "_id" in df.columns:
            df.drop(columns=["_id"], inplace=True)
        
        return df
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error while fetching review data: {str(e)}"
        )

def save_dataframe_to_csv(df: pd.DataFrame, file_path: str) -> None:
    """Save DataFrame to CSV file."""
    try:
        df.to_csv(file_path, index=False, encoding="utf-8")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving data to temporary file: {str(e)}"
        )

def process_reviews(processor_class, input_path: str, output_path: str) -> pd.DataFrame:
    """Process reviews using the specified processor."""
    try:
        processor = processor_class(input_path=input_path, output_path=output_path)
        processor.preprocess()
        processor.feature_engineering()
        return processor.df
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during review processing: {str(e)}"
        )

def save_processed_data(processed_data: List[Dict[str, Any]], collection_name: str) -> None:
    """Save processed data to MongoDB."""
    try:
        processed_collection = mongo_db[collection_name]
        
        # Remove any _id fields from processed data
        cleaned_data = []
        for item in processed_data:
            cleaned_item = {k: v for k, v in item.items() if k != "_id"}
            cleaned_data.append(cleaned_item)
        
        if cleaned_data:
            processed_collection.insert_many(cleaned_data)
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving processed data to database: {str(e)}"
        )

@review.post("/preprocess/{site_name}", status_code=status.HTTP_200_OK)
def preprocess_review(site_name: str) -> BaseResponse:
    """
    Preprocess reviews from the specified site.
    
    Args:
        site_name: Name of the review site (kakaomap, myrealtrip, tripdotcom)
        
    Returns:
        BaseResponse with processed review data
    """
    # Validate site name
    site_name = validate_site_name(site_name)
    
    # Collection names
    source_collection = f"review_{site_name}"
    target_collection = f"preprocessed_reviews_{site_name}"
    
    try:
        # Fetch data from MongoDB
        df = fetch_review_data(source_collection)
        
        # Use temporary files with automatic cleanup
        with temporary_files(".csv", "_out.csv") as (input_path, output_path):
            # Save DataFrame to temporary CSV
            save_dataframe_to_csv(df, input_path)
            
            # Get processor class and process reviews
            processor_class = SITE_PROCESSORS[site_name]
            processed_df = process_reviews(processor_class, input_path, output_path)
            
            # Convert processed DataFrame to records
            processed_data = processed_df.to_dict(orient="records")
            
            # Save processed data to MongoDB
            save_processed_data(processed_data, target_collection)
            
            return BaseResponse(
                status="success",
                data={
                    "processed_count": len(processed_data),
                    "site_name": site_name,
                    "source_collection": source_collection,
                    "target_collection": target_collection
                },
                message=f"Review preprocessing completed successfully for {site_name}. Processed {len(processed_data)} records."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during preprocessing: {str(e)}"
        )