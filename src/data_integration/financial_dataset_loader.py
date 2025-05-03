"""
Financial dataset loader.

This module provides utilities for loading and preparing pre-labeled
financial datasets for use in the AI system.
"""

import os
import json
import pandas as pd
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialDatasetLoader:
    """
    Loads and prepares pre-labeled financial datasets.
    
    Features:
    - Supports multiple dataset formats (CSV, JSON, etc.)
    - Preprocessing and normalization options
    - Dataset splitting (train/validation)
    - Label handling
    """
    
    def __init__(
        self,
        dataset_dir: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the dataset loader.
        
        Args:
            dataset_dir: Optional directory containing financial datasets
            cache_dir: Optional directory for caching processed datasets
        """
        self.dataset_dir = dataset_dir or os.path.join(os.getcwd(), "data", "datasets")
        self.cache_dir = cache_dir or os.path.join(os.getcwd(), "data", "cache")
        
        # Create directories if they don't exist
        os.makedirs(self.dataset_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Mapping of dataset type to handler
        self.dataset_handlers = {
            "financial_statements": self._load_financial_statements,
            "market_data": self._load_market_data,
            "sentiment_labeled": self._load_sentiment_data,
            "news_articles": self._load_news_data,
            "sec_filings": self._load_sec_filings
        }
        
        logger.info(f"FinancialDatasetLoader initialized with dataset_dir: {self.dataset_dir}")
    
    def list_available_datasets(self) -> List[Dict[str, Any]]:
        """
        List all available datasets in the dataset directory.
        
        Returns:
            List of dataset info dictionaries
        """
        datasets = []
        
        for root, dirs, files in os.walk(self.dataset_dir):
            for file in files:
                if file.endswith((".csv", ".json", ".parquet", ".xlsx")):
                    path = os.path.join(root, file)
                    rel_path = os.path.relpath(path, self.dataset_dir)
                    
                    # Try to determine dataset type from directory structure
                    parts = rel_path.split(os.sep)
                    dataset_type = parts[0] if len(parts) > 1 else "unknown"
                    
                    size = os.path.getsize(path) / (1024 * 1024)  # Size in MB
                    
                    datasets.append({
                        "name": os.path.splitext(file)[0],
                        "path": rel_path,
                        "type": dataset_type,
                        "format": os.path.splitext(file)[1][1:],
                        "size_mb": round(size, 2)
                    })
        
        return datasets
    
    def load_dataset(
        self,
        dataset_name: str,
        dataset_type: Optional[str] = None,
        preprocessed: bool = True,
        split: Optional[str] = None
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Load a dataset by name.
        
        Args:
            dataset_name: Name of the dataset
            dataset_type: Type of financial dataset (autodetected if None)
            preprocessed: Whether to apply preprocessing
            split: Dataset split to load ('train', 'val', 'test', or None for all)
            
        Returns:
            DataFrame or dictionary of DataFrames
        """
        # Find the dataset path
        dataset_path = self._find_dataset_path(dataset_name)
        if not dataset_path:
            available = [d["name"] for d in self.list_available_datasets()]
            raise ValueError(f"Dataset '{dataset_name}' not found. Available datasets: {available}")
        
        # Determine dataset type if not provided
        if dataset_type is None:
            dataset_type = self._detect_dataset_type(dataset_path)
            logger.info(f"Autodetected dataset type: {dataset_type}")
        
        # Check if we have a preprocessed cached version
        cache_key = f"{dataset_name}_{dataset_type}"
        if preprocessed and self._check_cache(cache_key):
            logger.info(f"Loading preprocessed dataset from cache: {cache_key}")
            data = self._load_from_cache(cache_key, split)
            return data
        
        # Load the dataset using the appropriate handler
        if dataset_type in self.dataset_handlers:
            data = self.dataset_handlers[dataset_type](dataset_path)
        else:
            # Default loading method
            data = self._load_generic_dataset(dataset_path)
        
        # Preprocess if requested
        if preprocessed:
            data = self._preprocess_dataset(data, dataset_type)
            # Cache the preprocessed data
            self._save_to_cache(data, cache_key)
        
        # Return the requested split
        if split:
            if isinstance(data, dict) and split in data:
                return data[split]
            elif isinstance(data, pd.DataFrame):
                # If no splits exist but split is requested, create splits
                return self._create_splits(data)[split]
            else:
                raise ValueError(f"Split '{split}' not available in dataset")
        
        return data
    
    def _find_dataset_path(self, dataset_name: str) -> Optional[str]:
        """
        Find the full path to a dataset by name.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Full path to dataset file or None if not found
        """
        # First look for exact filename match
        for root, _, files in os.walk(self.dataset_dir):
            for file in files:
                name_without_ext = os.path.splitext(file)[0]
                if name_without_ext == dataset_name:
                    return os.path.join(root, file)
        
        # Then look for directory with the name
        potential_dir = os.path.join(self.dataset_dir, dataset_name)
        if os.path.isdir(potential_dir):
            # Look for main dataset file (e.g., data.csv)
            for standard_name in ["data.csv", "data.json", "data.parquet", "dataset.csv"]:
                if os.path.exists(os.path.join(potential_dir, standard_name)):
                    return os.path.join(potential_dir, standard_name)
        
        return None
    
    def _detect_dataset_type(self, dataset_path: str) -> str:
        """
        Detect the type of dataset based on path and content.
        
        Args:
            dataset_path: Path to the dataset file
            
        Returns:
            Dataset type string
        """
        # Check if type is in the path
        path_parts = dataset_path.split(os.sep)
        for part in path_parts:
            for dataset_type in self.dataset_handlers.keys():
                if dataset_type in part.lower():
                    return dataset_type
        
        # Peek at the data to determine type
        if dataset_path.endswith(".csv"):
            df = pd.read_csv(dataset_path, nrows=5)
            
            # Check column names for clues
            columns = [col.lower() for col in df.columns]
            
            if any(col in columns for col in ["sentiment", "label"]):
                return "sentiment_labeled"
            elif any(col in columns for col in ["assets", "liabilities", "equity"]):
                return "financial_statements"
            elif any(col in columns for col in ["open", "high", "low", "close", "volume"]):
                return "market_data"
            elif any(col in columns for col in ["headline", "title", "article", "body"]):
                return "news_articles"
        
        # Default type
        return "generic"
    
    def _check_cache(self, cache_key: str) -> bool:
        """
        Check if a cached version of the dataset exists.
        
        Args:
            cache_key: Cache identifier
            
        Returns:
            True if cached version exists
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.parquet")
        return os.path.exists(cache_path)
    
    def _load_from_cache(
        self,
        cache_key: str,
        split: Optional[str] = None
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Load dataset from cache.
        
        Args:
            cache_key: Cache identifier
            split: Dataset split to load
            
        Returns:
            DataFrame or dictionary of DataFrames
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.parquet")
        data = pd.read_parquet(cache_path)
        
        # Check if this is a dataset with splits
        if "split" in data.columns:
            # Return the specified split or all splits
            if split:
                return data[data["split"] == split].drop(columns=["split"])
            else:
                # Return dictionary of splits
                splits = {}
                for s in data["split"].unique():
                    splits[s] = data[data["split"] == s].drop(columns=["split"])
                return splits
        
        # No splits, return entire dataset
        return data
    
    def _save_to_cache(self, data: Union[pd.DataFrame, Dict[str, pd.DataFrame]], cache_key: str):
        """
        Save processed dataset to cache.
        
        Args:
            data: DataFrame or dictionary of DataFrames
            cache_key: Cache identifier
        """
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.parquet")
        
        # If it's a dictionary of splits, combine them with a split column
        if isinstance(data, dict):
            combined_data = pd.DataFrame()
            for split_name, split_data in data.items():
                split_data = split_data.copy()
                split_data["split"] = split_name
                combined_data = pd.concat([combined_data, split_data])
            data = combined_data
        
        # Save to parquet
        data.to_parquet(cache_path, index=False)
        logger.info(f"Saved processed dataset to cache: {cache_path}")
    
    def _create_splits(
        self,
        data: pd.DataFrame,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        random_state: int = 42
    ) -> Dict[str, pd.DataFrame]:
        """
        Create train/val/test splits from a dataset.
        
        Args:
            data: DataFrame to split
            train_ratio: Proportion for training
            val_ratio: Proportion for validation
            test_ratio: Proportion for testing
            random_state: Random seed for reproducibility
            
        Returns:
            Dictionary of DataFrames with splits
        """
        # Shuffle the data
        data = data.sample(frac=1, random_state=random_state).reset_index(drop=True)
        
        # Calculate split indices
        n = len(data)
        train_end = int(train_ratio * n)
        val_end = train_end + int(val_ratio * n)
        
        # Create splits
        splits = {
            "train": data.iloc[:train_end].copy(),
            "val": data.iloc[train_end:val_end].copy(),
            "test": data.iloc[val_end:].copy()
        }
        
        return splits
    
    def _preprocess_dataset(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        dataset_type: str
    ) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """
        Preprocess dataset based on its type.
        
        Args:
            data: DataFrame or dictionary of DataFrames
            dataset_type: Type of dataset
            
        Returns:
            Preprocessed data
        """
        # If it's a dictionary of splits, preprocess each split
        if isinstance(data, dict):
            return {k: self._preprocess_single_df(v, dataset_type) for k, v in data.items()}
        
        # Otherwise preprocess the single DataFrame
        return self._preprocess_single_df(data, dataset_type)
    
    def _preprocess_single_df(self, df: pd.DataFrame, dataset_type: str) -> pd.DataFrame:
        """
        Preprocess a single DataFrame.
        
        Args:
            df: DataFrame to preprocess
            dataset_type: Type of dataset
            
        Returns:
            Preprocessed DataFrame
        """
        # Make a copy to avoid modifying the original
        df = df.copy()
        
        # Common preprocessing
        # 1. Handle missing values
        for col in df.columns:
            if df[col].dtype == 'object' or df[col].dtype == 'string':
                df[col] = df[col].fillna("")
            else:
                df[col] = df[col].fillna(0)
        
        # 2. Drop duplicates
        df = df.drop_duplicates()
        
        # Type-specific preprocessing
        if dataset_type == "financial_statements":
            # Ensure numeric columns are numeric
            for col in df.columns:
                if col not in ['company', 'ticker', 'date', 'period', 'year', 'quarter']:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except:
                        pass
                        
        elif dataset_type == "market_data":
            # Convert date columns to datetime
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='ignore')
                    
        elif dataset_type == "sentiment_labeled":
            # Normalize sentiment labels
            if 'sentiment' in df.columns:
                # Map text labels to numeric values if needed
                sentiment_map = {
                    'positive': 1,
                    'neutral': 0,
                    'negative': -1,
                    'bullish': 1,
                    'bearish': -1
                }
                
                # Only apply mapping if column contains strings
                if df['sentiment'].dtype == 'object':
                    df['sentiment'] = df['sentiment'].map(
                        lambda x: sentiment_map.get(str(x).lower(), x)
                    )
        
        return df
    
    # Dataset type-specific loading methods
    def _load_financial_statements(self, dataset_path: str) -> pd.DataFrame:
        """Load financial statement data."""
        ext = os.path.splitext(dataset_path)[1].lower()
        
        if ext == '.csv':
            return pd.read_csv(dataset_path)
        elif ext == '.json':
            return pd.read_json(dataset_path)
        elif ext == '.parquet':
            return pd.read_parquet(dataset_path)
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(dataset_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _load_market_data(self, dataset_path: str) -> pd.DataFrame:
        """Load market data (prices, volumes, etc.)."""
        df = self._load_generic_dataset(dataset_path)
        
        # Convert date columns to datetime
        for col in df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='ignore')
        
        return df
    
    def _load_sentiment_data(self, dataset_path: str) -> pd.DataFrame:
        """Load sentiment-labeled data."""
        return self._load_generic_dataset(dataset_path)
    
    def _load_news_data(self, dataset_path: str) -> pd.DataFrame:
        """Load financial news articles."""
        return self._load_generic_dataset(dataset_path)
    
    def _load_sec_filings(self, dataset_path: str) -> pd.DataFrame:
        """Load SEC filing data."""
        return self._load_generic_dataset(dataset_path)
    
    def _load_generic_dataset(self, dataset_path: str) -> pd.DataFrame:
        """Generic dataset loading method based on file extension."""
        ext = os.path.splitext(dataset_path)[1].lower()
        
        if ext == '.csv':
            return pd.read_csv(dataset_path)
        elif ext == '.json':
            return pd.read_json(dataset_path)
        elif ext == '.parquet':
            return pd.read_parquet(dataset_path)
        elif ext in ['.xlsx', '.xls']:
            return pd.read_excel(dataset_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def export_dataset(
        self,
        data: Union[pd.DataFrame, Dict[str, pd.DataFrame]],
        export_path: str,
        format: str = 'csv'
    ):
        """
        Export a dataset to a file.
        
        Args:
            data: DataFrame or dictionary of DataFrames
            export_path: Path to export to
            format: Export format ('csv', 'json', 'parquet')
        """
        os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
        
        if isinstance(data, dict):
            # Export each split to a separate file
            for split_name, split_data in data.items():
                split_path = f"{os.path.splitext(export_path)[0]}_{split_name}.{format}"
                self._export_single_df(split_data, split_path, format)
        else:
            # Export the single DataFrame
            self._export_single_df(data, export_path, format)
    
    def _export_single_df(self, df: pd.DataFrame, path: str, format: str):
        """Export a single DataFrame to a file."""
        if format == 'csv':
            df.to_csv(path, index=False)
        elif format == 'json':
            df.to_json(path, orient='records')
        elif format == 'parquet':
            df.to_parquet(path, index=False)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Exported dataset to {path}") 