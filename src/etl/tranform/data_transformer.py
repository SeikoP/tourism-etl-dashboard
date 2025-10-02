#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_data: Dict[str, Any]

class DataTransformer:
    """Transform and validate extracted hotel data"""

    def __init__(self):
        # Validation rules
        self.min_name_length = 2
        self.max_name_length = 200
        self.valid_currencies = ['VND', 'USD', 'EUR']
        self.max_price = 100000000  # 100M VND max
        self.min_price = 10000      # 10K VND min

        # Vietnamese location mappings for normalization
        self.location_normalizations = {
            'TP.HCM': 'TP Hồ Chí Minh',
            'TPHCM': 'TP Hồ Chí Minh',
            'HCMC': 'TP Hồ Chí Minh',
            'Sài Gòn': 'TP Hồ Chí Minh',
            'Hà Nội': 'Hà Nội',
            'HN': 'Hà Nội',
            'Đà Nẵng': 'Đà Nẵng',
            'DN': 'Đà Nẵng',
            'Nha Trang': 'Nha Trang',
            'Đà Lạt': 'Đà Lạt',
            'Phú Quốc': 'Phú Quốc',
            'Sapa': 'Sapa',
            'Hội An': 'Hội An'
        }

    def transform_hotels_data(self, hotels_file: str, output_file: str) -> Dict[str, Any]:
        """Transform and validate hotels data"""

        logger.info(f"Transforming hotels data from {hotels_file}")

        # Load data
        with open(hotels_file, 'r', encoding='utf-8') as f:
            hotels = json.load(f)

        transformed_hotels = []
        stats = {
            'total': len(hotels),
            'valid': 0,
            'invalid': 0,
            'warnings': 0,
            'errors': []
        }

        for hotel in hotels:
            result = self._validate_and_clean_hotel(hotel)

            if result.is_valid:
                transformed_hotels.append(result.cleaned_data)
                stats['valid'] += 1
                if result.warnings:
                    stats['warnings'] += len(result.warnings)
            else:
                stats['invalid'] += 1
                stats['errors'].extend(result.errors)

        # Save transformed data
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_hotels, f, ensure_ascii=False, indent=2)

        stats['output_file'] = output_file
        logger.info(f"Transformation complete: {stats['valid']} valid, {stats['invalid']} invalid hotels")

        return stats

    def transform_hotel_details_data(self, details_dir: str, output_file: str) -> Dict[str, Any]:
        """Transform and validate hotel details data"""

        logger.info(f"Transforming hotel details from {details_dir}")

        # Find all detail files
        detail_files = []
        for file in os.listdir(details_dir):
            if file.startswith('ai_hotel_details_batch_') and file.endswith('.json'):
                detail_files.append(os.path.join(details_dir, file))

        all_details = []
        stats = {
            'total_files': len(detail_files),
            'total_details': 0,
            'valid': 0,
            'invalid': 0,
            'warnings': 0,
            'errors': []
        }

        for file_path in detail_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    batch_details = json.load(f)

                stats['total_details'] += len(batch_details)

                for detail in batch_details:
                    result = self._validate_and_clean_hotel_detail(detail)

                    if result.is_valid:
                        all_details.append(result.cleaned_data)
                        stats['valid'] += 1
                        if result.warnings:
                            stats['warnings'] += len(result.warnings)
                    else:
                        stats['invalid'] += 1
                        stats['errors'].extend(result.errors)

            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                stats['errors'].append(f"File processing error: {file_path} - {str(e)}")

        # Save transformed data
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_details, f, ensure_ascii=False, indent=2)

        stats['output_file'] = output_file
        logger.info(f"Details transformation complete: {stats['valid']} valid, {stats['invalid']} invalid details")

        return stats

    def _validate_and_clean_hotel(self, hotel: Dict[str, Any]) -> ValidationResult:
        """Validate and clean a single hotel record"""

        errors = []
        warnings = []
        cleaned = hotel.copy()

        # Validate required fields
        required_fields = ['location_name', 'location_code', 'url', 'name']
        for field in required_fields:
            if not hotel.get(field):
                errors.append(f"Missing required field: {field}")
            elif not isinstance(hotel[field], str):
                errors.append(f"Field {field} must be string")

        if errors:
            return ValidationResult(False, errors, warnings, {})

        # Clean and validate name
        name = hotel['name'].strip()
        if len(name) < self.min_name_length:
            errors.append(f"Hotel name too short: {len(name)} chars")
        elif len(name) > self.max_name_length:
            warnings.append(f"Hotel name truncated from {len(name)} to {self.max_name_length} chars")
            name = name[:self.max_name_length]

        cleaned['name'] = name

        # Validate and normalize location
        location_name = hotel['location_name'].strip()
        location_code = hotel['location_code'].strip()

        # Normalize location name
        normalized_location = self.location_normalizations.get(location_name, location_name)
        cleaned['location_name'] = normalized_location

        # Validate location code format
        if not re.match(r'^[a-z0-9-]+$', location_code):
            warnings.append(f"Location code format may be invalid: {location_code}")

        cleaned['location_code'] = location_code.lower()

        # Validate URL
        url = hotel['url'].strip()
        if not url.startswith('http'):
            errors.append(f"Invalid URL format: {url}")
        elif 'vietnambooking.com' not in url:
            warnings.append(f"URL may not be from VietnamBooking: {url}")

        cleaned['url'] = url

        # Add metadata
        cleaned['transformed_at'] = datetime.now().isoformat()
        cleaned['data_quality_score'] = self._calculate_quality_score(cleaned, warnings)

        return ValidationResult(True, errors, warnings, cleaned)

    def _validate_and_clean_hotel_detail(self, detail: Dict[str, Any]) -> ValidationResult:
        """Validate and clean a single hotel detail record"""

        errors = []
        warnings = []
        cleaned = detail.copy()

        # Check basic info
        basic_info = detail.get('basic_info', {})
        if not basic_info:
            errors.append("Missing basic_info section")
            return ValidationResult(False, errors, warnings, {})

        # Validate required basic fields
        required_basic = ['location_name', 'location_code', 'url', 'name']
        for field in required_basic:
            if not basic_info.get(field):
                errors.append(f"Missing required basic field: {field}")

        if errors:
            return ValidationResult(False, errors, warnings, {})

        # Clean extracted data
        extracted_data = detail.get('extracted_data', {})

        # Validate and clean address
        if extracted_data.get('address'):
            address = extracted_data['address'].strip()
            if len(address) > 500:
                warnings.append("Address truncated to 500 characters")
                address = address[:500]
            cleaned['extracted_data']['address'] = address

        # Validate and clean phone
        if extracted_data.get('phone'):
            phone = self._normalize_phone(extracted_data['phone'])
            if not phone:
                warnings.append("Invalid phone number format removed")
                cleaned['extracted_data'].pop('phone', None)
            else:
                cleaned['extracted_data']['phone'] = phone

        # Validate price information
        if extracted_data.get('price_analysis'):
            price_analysis = extracted_data['price_analysis']
            if not self._validate_price_analysis(price_analysis):
                warnings.append("Invalid or unrealistic price analysis data - may contain parsing errors")
                cleaned['extracted_data'].pop('price_analysis', None)

                # Try to extract reasonable prices from price_range text if available
                if extracted_data.get('price_range'):
                    price_range_text = extracted_data['price_range']
                    # Look for VND amounts in the text (skip percentages and very low numbers)
                    import re
                    vnd_matches = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*VND', price_range_text, re.IGNORECASE)
                    reasonable_prices = []

                    for match in vnd_matches:
                        # Remove commas and convert to float
                        price_str = match.replace(',', '')
                        try:
                            price = float(price_str)
                            # Only consider prices that look reasonable for hotels (> 100K VND)
                            if price >= 100000:
                                reasonable_prices.append(price)
                        except ValueError:
                            continue

                    if reasonable_prices:
                        # Create a corrected price analysis
                        min_price = min(reasonable_prices)
                        max_price = max(reasonable_prices)
                        avg_price = sum(reasonable_prices) / len(reasonable_prices)

                        corrected_price_analysis = {
                            'min_price': min_price,
                            'max_price': max_price,
                            'avg_price': avg_price,
                            'price_count': len(reasonable_prices),
                            'currency': 'VND',
                            'formatted_range': f"{min_price:,.0f} - {max_price:,.0f} VND",
                            'corrected_from_text': True
                        }

                        cleaned['extracted_data']['price_analysis'] = corrected_price_analysis
                        warnings.append(f"Price analysis corrected from text parsing: {len(reasonable_prices)} valid prices found")
                    else:
                        warnings.append("Could not extract reasonable prices from price_range text")

        # Clean amenities - check for missing or empty amenities
        if not extracted_data.get('basic_amenities') or len(extracted_data.get('basic_amenities', [])) == 0:
            warnings.append("No amenities data found - hotel details may be incomplete")

        if extracted_data.get('basic_amenities'):
            amenities = extracted_data['basic_amenities']
            if isinstance(amenities, list):
                # Remove duplicates and empty items
                cleaned_amenities = list(set([a.strip() for a in amenities if a.strip()]))
                if len(cleaned_amenities) == 0:
                    warnings.append("All amenities data was empty or invalid")
                else:
                    cleaned['extracted_data']['basic_amenities'] = cleaned_amenities[:20]  # Limit to 20
            else:
                warnings.append("Amenities data is not in expected list format")
                cleaned['extracted_data'].pop('basic_amenities', None)

        # Add metadata
        cleaned['transformed_at'] = datetime.now().isoformat()
        cleaned['data_quality_score'] = self._calculate_detail_quality_score(cleaned, warnings)

        return ValidationResult(True, errors, warnings, cleaned)

    def _normalize_phone(self, phone: str) -> Optional[str]:
        """Normalize phone number format"""

        if not phone:
            return None

        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)

        # Handle Vietnamese phone numbers
        if cleaned.startswith('84'):
            return f"+{cleaned}"
        elif cleaned.startswith('0'):
            return f"+84{cleaned[1:]}"
        elif len(cleaned) == 9 or len(cleaned) == 10:
            return f"+84{cleaned}"

        return None

    def _validate_price_analysis(self, price_analysis: Dict[str, Any]) -> bool:
        """Validate price analysis data"""

        required_fields = ['min_price', 'max_price', 'avg_price', 'currency']
        for field in required_fields:
            if field not in price_analysis:
                return False

        # Validate price ranges
        min_price = price_analysis['min_price']
        max_price = price_analysis['max_price']
        avg_price = price_analysis['avg_price']

        # Check for unrealistic prices (too low for hotels)
        min_reasonable_price = 100000  # 100K VND minimum for hotels
        if min_price < min_reasonable_price and min_price > 0:
            # This might be a percentage parsed as price (e.g., "54%" -> 54.0)
            return False

        if not (self.min_price <= min_price <= self.max_price):
            return False
        if not (self.min_price <= max_price <= self.max_price):
            return False
        if not (self.min_price <= avg_price <= self.max_price):
            return False
        if min_price > max_price:
            return False

        # Validate currency
        currency = price_analysis.get('currency', '').upper()
        if currency not in self.valid_currencies:
            return False

        return True

    def _calculate_quality_score(self, hotel: Dict[str, Any], warnings: List[str]) -> float:
        """Calculate data quality score (0-100)"""

        score = 100.0

        # Deduct for warnings
        score -= len(warnings) * 5

        # Deduct for missing optional fields
        optional_fields = ['rating', 'address', 'price_info']
        for field in optional_fields:
            if not hotel.get(field):
                score -= 10

        # Ensure score stays within bounds
        return max(0.0, min(100.0, score))

    def _calculate_detail_quality_score(self, detail: Dict[str, Any], warnings: List[str]) -> float:
        """Calculate detail data quality score"""

        score = 100.0

        # Deduct for warnings
        score -= len(warnings) * 5

        extracted_data = detail.get('extracted_data', {})

        # Bonus for rich data
        if extracted_data.get('address'):
            score += 5
        if extracted_data.get('phone'):
            score += 5
        if extracted_data.get('price_analysis'):
            score += 10
        if extracted_data.get('basic_amenities'):
            score += 5
        if extracted_data.get('description'):
            score += 5

        # Deduct for missing AI extraction
        if not detail.get('ai_extraction_success', False):
            score -= 15

        return max(0.0, min(100.0, score))