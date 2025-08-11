import json
import csv
import yaml
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import pandas as pd
from io import StringIO
import logging

from ..utils import setup_logging


logger = setup_logging("DataTransformers")


class DataTransformer:
    """Base class for data transformations"""
    
    @staticmethod
    def json_to_csv(data: Union[List[Dict], Dict], output_path: Optional[Path] = None) -> str:
        """Convert JSON data to CSV format"""
        if isinstance(data, dict):
            data = [data]
        
        if not data:
            return ""
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        csv_string = output.getvalue()
        
        if output_path:
            output_path.write_text(csv_string)
        
        return csv_string
    
    @staticmethod
    def csv_to_json(csv_data: str, output_path: Optional[Path] = None) -> List[Dict]:
        """Convert CSV data to JSON format"""
        reader = csv.DictReader(StringIO(csv_data))
        json_data = list(reader)
        
        if output_path:
            output_path.write_text(json.dumps(json_data, indent=2))
        
        return json_data
    
    @staticmethod
    def json_to_yaml(data: Any, output_path: Optional[Path] = None) -> str:
        """Convert JSON data to YAML format"""
        yaml_string = yaml.dump(data, default_flow_style=False, sort_keys=False)
        
        if output_path:
            output_path.write_text(yaml_string)
        
        return yaml_string
    
    @staticmethod
    def yaml_to_json(yaml_data: str, output_path: Optional[Path] = None) -> Any:
        """Convert YAML data to JSON format"""
        json_data = yaml.safe_load(yaml_data)
        
        if output_path:
            output_path.write_text(json.dumps(json_data, indent=2))
        
        return json_data
    
    @staticmethod
    def json_to_xml(data: Dict, root_name: str = "root", output_path: Optional[Path] = None) -> str:
        """Convert JSON data to XML format"""
        def dict_to_xml(tag: str, d: Any) -> ET.Element:
            elem = ET.Element(tag)
            
            if isinstance(d, dict):
                for key, val in d.items():
                    child = dict_to_xml(key, val)
                    elem.append(child)
            elif isinstance(d, list):
                for item in d:
                    child = dict_to_xml("item", item)
                    elem.append(child)
            else:
                elem.text = str(d)
            
            return elem
        
        root = dict_to_xml(root_name, data)
        xml_string = ET.tostring(root, encoding='unicode')
        
        if output_path:
            output_path.write_text(xml_string)
        
        return xml_string
    
    @staticmethod
    def xml_to_json(xml_data: str, output_path: Optional[Path] = None) -> Dict:
        """Convert XML data to JSON format"""
        def xml_to_dict(element: ET.Element) -> Any:
            if len(element) == 0:
                return element.text
            
            result = {}
            for child in element:
                child_data = xml_to_dict(child)
                
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            
            return result
        
        root = ET.fromstring(xml_data)
        json_data = {root.tag: xml_to_dict(root)}
        
        if output_path:
            output_path.write_text(json.dumps(json_data, indent=2))
        
        return json_data
    
    @staticmethod
    def flatten_json(data: Dict, separator: str = "_") -> Dict:
        """Flatten nested JSON structure"""
        def flatten(obj: Any, prefix: str = "") -> Dict:
            result = {}
            
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_key = f"{prefix}{separator}{key}" if prefix else key
                    result.update(flatten(value, new_key))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_key = f"{prefix}{separator}{i}" if prefix else str(i)
                    result.update(flatten(item, new_key))
            else:
                result[prefix] = obj
            
            return result
        
        return flatten(data)
    
    @staticmethod
    def unflatten_json(data: Dict, separator: str = "_") -> Dict:
        """Unflatten a flattened JSON structure"""
        result = {}
        
        for key, value in data.items():
            parts = key.split(separator)
            current = result
            
            for part in parts[:-1]:
                if part not in current:
                    # Try to determine if it should be a list or dict
                    try:
                        int(part)
                        current[part] = []
                    except ValueError:
                        current[part] = {}
                current = current[part]
            
            current[parts[-1]] = value
        
        return result


class DataValidator:
    """Data validation utilities"""
    
    @staticmethod
    def validate_json_schema(data: Any, schema: Dict) -> Tuple[bool, List[str]]:
        """Validate data against JSON schema"""
        try:
            from jsonschema import validate, ValidationError
            
            errors = []
            try:
                validate(instance=data, schema=schema)
                return True, []
            except ValidationError as e:
                errors.append(str(e))
                return False, errors
        except ImportError:
            logger.warning("jsonschema not installed, skipping validation")
            return True, []
    
    @staticmethod
    def validate_required_fields(data: Dict, required_fields: List[str]) -> Tuple[bool, List[str]]:
        """Check if all required fields are present"""
        errors = []
        
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_data_types(data: Dict, type_map: Dict[str, type]) -> Tuple[bool, List[str]]:
        """Validate data types of fields"""
        errors = []
        
        for field, expected_type in type_map.items():
            if field in data:
                if not isinstance(data[field], expected_type):
                    errors.append(
                        f"Field '{field}' has wrong type. "
                        f"Expected {expected_type.__name__}, got {type(data[field]).__name__}"
                    )
        
        return len(errors) == 0, errors


class DataCleaner:
    """Data cleaning utilities"""
    
    @staticmethod
    def remove_nulls(data: Union[Dict, List]) -> Union[Dict, List]:
        """Remove null/None values from data"""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [item for item in data if item is not None]
        return data
    
    @staticmethod
    def remove_duplicates(data: List[Dict], key_field: Optional[str] = None) -> List[Dict]:
        """Remove duplicate entries from list"""
        if not data:
            return data
        
        if key_field:
            seen = set()
            unique = []
            for item in data:
                if key_field in item:
                    key = item[key_field]
                    if key not in seen:
                        seen.add(key)
                        unique.append(item)
            return unique
        else:
            # Remove exact duplicates
            unique = []
            for item in data:
                if item not in unique:
                    unique.append(item)
            return unique
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text (lowercase, trim, etc.)"""
        import re
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    @staticmethod
    def sanitize_html(html: str) -> str:
        """Remove HTML tags from text"""
        import re
        
        # Remove HTML tags
        clean = re.sub('<.*?>', '', html)
        
        # Decode HTML entities
        from html import unescape
        clean = unescape(clean)
        
        return clean


class DataAggregator:
    """Data aggregation utilities"""
    
    @staticmethod
    def aggregate_by_field(data: List[Dict], field: str) -> Dict[str, List[Dict]]:
        """Group data by a specific field"""
        result = {}
        
        for item in data:
            if field in item:
                key = item[field]
                if key not in result:
                    result[key] = []
                result[key].append(item)
        
        return result
    
    @staticmethod
    def calculate_statistics(data: List[Union[int, float]]) -> Dict[str, float]:
        """Calculate basic statistics for numerical data"""
        import statistics
        
        if not data:
            return {}
        
        return {
            "count": len(data),
            "sum": sum(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "min": min(data),
            "max": max(data),
            "std_dev": statistics.stdev(data) if len(data) > 1 else 0,
        }
    
    @staticmethod
    def merge_datasets(datasets: List[List[Dict]], key_field: str) -> List[Dict]:
        """Merge multiple datasets on a common key"""
        merged = {}
        
        for dataset in datasets:
            for item in dataset:
                if key_field in item:
                    key = item[key_field]
                    if key not in merged:
                        merged[key] = {}
                    merged[key].update(item)
        
        return list(merged.values())