"""
OBD-II Log Parser Service.
Implements BR2: New Chat Creation with Log Upload
"""

import pandas as pd
import re
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from enum import Enum

from ..config.logging_config import get_logger

logger = get_logger(__name__)


class OBDParseError(Exception):
    """Custom exception for OBD-II parsing errors."""
    pass


class MetricStatus(Enum):
    """Status classification for metrics."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class OBDMetric:
    """Represents a parsed OBD-II metric."""
    name: str
    value: float
    unit: str
    status: str = "normal"  # 'normal', 'warning', 'critical'
    pid: Optional[str] = None
    description: Optional[str] = None
    normal_range: Optional[str] = None
    timestamp: Optional[str] = None


@dataclass
class FaultCode:
    """Represents an OBD-II Diagnostic Trouble Code (DTC)."""
    code: str
    description: str
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'powertrain', 'chassis', 'body', 'network'
    is_generic: bool = True
    possible_causes: List[str] = field(default_factory=list)
    recommended_action: Optional[str] = None


class OBDParser:
    """
    Parser for OBD-II log files (CSV format).

    Supports:
    - BR2.1: User uploads a valid log file
    - BR2.2: User uploads an invalid file type
    - BR2.3: User uploads a valid file type with bad data
    """

    # Normal ranges for common OBD-II metrics
    METRIC_RANGES: Dict[str, Dict[str, float]] = {
        "engine_rpm": {
            "min": 600, "max": 7000,
            "warning_low": 400, "warning_high": 6500,
            "critical_low": 200, "critical_high": 7500
        },
        "coolant_temp": {
            "min": 70, "max": 105,
            "warning_low": 50, "warning_high": 110,
            "critical_low": 30, "critical_high": 120
        },
        "vehicle_speed": {
            "min": 0, "max": 200,
            "warning_low": 0, "warning_high": 180,
            "critical_low": 0, "critical_high": 220
        },
        "throttle_position": {
            "min": 0, "max": 100,
            "warning_low": 0, "warning_high": 95,
            "critical_low": 0, "critical_high": 100
        },
        "engine_load": {
            "min": 0, "max": 80,
            "warning_low": 0, "warning_high": 85,
            "critical_low": 0, "critical_high": 95
        },
        "fuel_level": {
            "min": 10, "max": 100,
            "warning_low": 5, "warning_high": 100,
            "critical_low": 0, "critical_high": 100
        },
        "intake_air_temp": {
            "min": -20, "max": 60,
            "warning_low": -30, "warning_high": 70,
            "critical_low": -40, "critical_high": 80
        },
        "maf_rate": {
            "min": 2, "max": 300,
            "warning_low": 1, "warning_high": 400,
            "critical_low": 0, "critical_high": 500
        },
        "fuel_pressure": {
            "min": 250, "max": 450,
            "warning_low": 200, "warning_high": 500,
            "critical_low": 100, "critical_high": 600
        },
        "battery_voltage": {
            "min": 12.4, "max": 14.7,
            "warning_low": 11.8, "warning_high": 15.0,
            "critical_low": 11.0, "critical_high": 16.0
        }
    }

    # Generic OBD-II fault code definitions
    FAULT_CODE_DATABASE: Dict[str, Tuple[str, str, List[str]]] = {
        # Fuel and Air Metering
        "P0100": ("Mass Air Flow Circuit Malfunction", "warning", ["Dirty MAF sensor", "Air leak", "Wiring issue"]),
        "P0101": ("Mass Air Flow Circuit Range/Performance", "warning", ["Dirty MAF sensor", "Vacuum leak"]),
        "P0102": ("Mass Air Flow Circuit Low Input", "warning", ["Sensor failure", "Wiring open circuit"]),
        "P0103": ("Mass Air Flow Circuit High Input", "warning", ["Sensor failure", "Short circuit"]),
        "P0104": ("Mass Air Flow Circuit Intermittent", "warning", ["Loose connection", "Damaged wiring"]),

        # Coolant Temperature
        "P0115": ("Engine Coolant Temperature Circuit Malfunction", "critical", ["Sensor failure", "Wiring issue"]),
        "P0116": ("Engine Coolant Temperature Circuit Range/Performance", "warning", ["Thermostat stuck", "Sensor drift"]),
        "P0117": ("Engine Coolant Temperature Circuit Low Input", "warning", ["Short to ground", "Sensor failure"]),
        "P0118": ("Engine Coolant Temperature Circuit High Input", "critical", ["Open circuit", "Sensor failure"]),
        "P0119": ("Engine Coolant Temperature Circuit Intermittent", "warning", ["Loose connection"]),

        # Throttle Position
        "P0120": ("Throttle Position Sensor Circuit Malfunction", "critical", ["TPS failure", "Wiring damage"]),
        "P0121": ("Throttle Position Sensor Range/Performance", "warning", ["TPS wear", "Calibration needed"]),
        "P0122": ("Throttle Position Sensor Circuit Low Input", "critical", ["Short to ground"]),
        "P0123": ("Throttle Position Sensor Circuit High Input", "critical", ["Open circuit"]),

        # Oxygen Sensors
        "P0130": ("O2 Sensor Circuit Malfunction (Bank 1 Sensor 1)", "warning", ["Sensor aging", "Exhaust leak"]),
        "P0131": ("O2 Sensor Circuit Low Voltage (Bank 1 Sensor 1)", "warning", ["Lean condition", "Sensor failure"]),
        "P0132": ("O2 Sensor Circuit High Voltage (Bank 1 Sensor 1)", "warning", ["Rich condition", "Sensor failure"]),
        "P0133": ("O2 Sensor Circuit Slow Response (Bank 1 Sensor 1)", "warning", ["Sensor aging"]),
        "P0134": ("O2 Sensor Circuit No Activity (Bank 1 Sensor 1)", "warning", ["Sensor failure", "Wiring issue"]),

        # Fuel System
        "P0169": ("Incorrect Fuel Composition", "warning", ["Wrong fuel type", "Contaminated fuel"]),
        "P0170": ("Fuel Trim Malfunction (Bank 1)", "warning", ["Vacuum leak", "Fuel pressure issue"]),
        "P0171": ("System Too Lean (Bank 1)", "warning", ["Vacuum leak", "Low fuel pressure", "MAF issue"]),
        "P0172": ("System Too Rich (Bank 1)", "warning", ["Leaking injector", "High fuel pressure"]),

        # Misfire
        "P0300": ("Random/Multiple Cylinder Misfire Detected", "critical", ["Spark plugs", "Ignition coils", "Fuel injectors"]),
        "P0301": ("Cylinder 1 Misfire Detected", "critical", ["Spark plug", "Ignition coil", "Injector"]),
        "P0302": ("Cylinder 2 Misfire Detected", "critical", ["Spark plug", "Ignition coil", "Injector"]),
        "P0303": ("Cylinder 3 Misfire Detected", "critical", ["Spark plug", "Ignition coil", "Injector"]),
        "P0304": ("Cylinder 4 Misfire Detected", "critical", ["Spark plug", "Ignition coil", "Injector"]),

        # Catalytic Converter
        "P0420": ("Catalyst System Efficiency Below Threshold (Bank 1)", "warning", ["Catalytic converter wear", "O2 sensor issue"]),
        "P0421": ("Warm Up Catalyst Efficiency Below Threshold (Bank 1)", "warning", ["Catalytic converter"]),
        "P0430": ("Catalyst System Efficiency Below Threshold (Bank 2)", "warning", ["Catalytic converter wear"]),

        # Vehicle Speed
        "P0500": ("Vehicle Speed Sensor Malfunction", "warning", ["VSS failure", "Wiring issue"]),
        "P0501": ("Vehicle Speed Sensor Range/Performance", "warning", ["VSS calibration"]),
        "P0505": ("Idle Control System Malfunction", "warning", ["Idle air control valve", "Vacuum leak"]),

        # Evaporative System
        "P0440": ("Evaporative Emission Control System Malfunction", "info", ["Gas cap loose", "EVAP leak"]),
        "P0441": ("Evaporative Emission Control System Incorrect Purge Flow", "info", ["Purge valve"]),
        "P0442": ("Evaporative Emission Control System Leak Detected (small leak)", "info", ["Small EVAP leak"]),
        "P0443": ("Evaporative Emission Control System Purge Control Valve Circuit", "info", ["Purge valve circuit"]),
        "P0446": ("Evaporative Emission Control System Vent Control Circuit", "info", ["Vent valve"]),
        "P0455": ("Evaporative Emission Control System Leak Detected (large leak)", "warning", ["Large EVAP leak", "Gas cap missing"]),

        # Transmission
        "P0700": ("Transmission Control System Malfunction", "warning", ["TCM issue", "Wiring"]),
        "P0715": ("Input/Turbine Speed Sensor Circuit Malfunction", "warning", ["Speed sensor"]),
        "P0720": ("Output Speed Sensor Circuit Malfunction", "warning", ["Speed sensor"]),
        "P0730": ("Incorrect Gear Ratio", "critical", ["Transmission wear", "Low fluid"]),
        "P0740": ("Torque Converter Clutch Circuit Malfunction", "warning", ["TCC solenoid"]),
    }

    # Column name mappings (various CSV formats)
    COLUMN_MAPPINGS: Dict[str, List[str]] = {
        "engine_rpm": ["engine_rpm", "rpm", "engine rpm", "eng_rpm", "ENGINE_RPM", "RPM"],
        "coolant_temp": ["coolant_temp", "coolant_temperature", "ect", "engine_coolant_temp", "COOLANT_TEMP"],
        "vehicle_speed": ["vehicle_speed", "speed", "vss", "VEHICLE_SPEED", "SPEED"],
        "throttle_position": ["throttle_position", "throttle", "tps", "THROTTLE_POSITION", "TPS"],
        "engine_load": ["engine_load", "load", "calculated_load", "ENGINE_LOAD", "LOAD"],
        "fuel_level": ["fuel_level", "fuel", "fuel_tank_level", "FUEL_LEVEL"],
        "intake_air_temp": ["intake_air_temp", "iat", "intake_temp", "INTAKE_AIR_TEMP", "IAT"],
        "maf_rate": ["maf_rate", "maf", "mass_air_flow", "MAF_RATE", "MAF"],
        "fuel_pressure": ["fuel_pressure", "fp", "FUEL_PRESSURE"],
        "battery_voltage": ["battery_voltage", "battery", "voltage", "BATTERY_VOLTAGE"],
        "fault_codes": ["fault_codes", "dtc", "trouble_codes", "FAULT_CODES", "DTC", "codes"],
        "timestamp": ["timestamp", "time", "datetime", "TIMESTAMP", "TIME"],
    }

    # Unit mappings
    METRIC_UNITS: Dict[str, str] = {
        "engine_rpm": "RPM",
        "coolant_temp": "°C",
        "vehicle_speed": "km/h",
        "throttle_position": "%",
        "engine_load": "%",
        "fuel_level": "%",
        "intake_air_temp": "°C",
        "maf_rate": "g/s",
        "fuel_pressure": "kPa",
        "battery_voltage": "V",
    }

    METRIC_DESCRIPTIONS: Dict[str, str] = {
        "engine_rpm": "Engine revolutions per minute",
        "coolant_temp": "Engine coolant temperature",
        "vehicle_speed": "Current vehicle speed",
        "throttle_position": "Throttle pedal position percentage",
        "engine_load": "Calculated engine load percentage",
        "fuel_level": "Fuel tank level percentage",
        "intake_air_temp": "Intake manifold air temperature",
        "maf_rate": "Mass air flow rate",
        "fuel_pressure": "Fuel rail pressure",
        "battery_voltage": "Battery/charging system voltage",
    }

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if a file is a valid OBD-II log (BR2.1, BR2.2, BR2.3).

        Args:
            file_path: Path to the file to validate

        Returns:
            Tuple of (is_valid, message)
        """
        path = Path(file_path)

        # Check file exists
        if not path.exists():
            return False, "File does not exist"

        # Check file extension (BR2.2)
        if path.suffix.lower() != ".csv":
            return False, "File must be a .csv file. Please upload a valid OBD-II log file."

        # Try to parse the file
        try:
            df = pd.read_csv(file_path)

            if df.empty:
                return False, "File is empty. Please upload a valid OBD-II log file."

            # Check for valid OBD-II columns (BR2.3)
            valid_columns = self._find_valid_columns(df)
            if not valid_columns:
                return False, "No valid OBD-II data found in file. Please ensure your CSV contains OBD-II metrics."

            return True, f"Valid OBD-II log file with {len(valid_columns)} metrics detected."

        except pd.errors.EmptyDataError:
            return False, "File is empty or corrupted."
        except pd.errors.ParserError:
            return False, "File is not a valid CSV format."
        except Exception as e:
            logger.error(f"Error validating file: {e}")
            return False, f"Error reading file: {str(e)}"

    def parse_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Parse an OBD-II CSV log file.

        Args:
            file_path: Path to the CSV file

        Returns:
            Dictionary containing parsed metrics, fault codes, and statistics

        Raises:
            OBDParseError: If parsing fails
        """
        # Validate first
        is_valid, message = self.validate_file(file_path)
        if not is_valid:
            raise OBDParseError(message)

        try:
            df = pd.read_csv(file_path)
            logger.info(f"Parsing OBD-II log: {file_path} ({len(df)} rows)")

            # Extract metrics
            metrics = self._extract_metrics(df)

            # Extract fault codes
            fault_codes = self._extract_fault_codes(df)

            # Calculate statistics
            stats = self._calculate_statistics(df, metrics)

            result = {
                "file_path": file_path,
                "row_count": len(df),
                "metrics": [m.__dict__ for m in metrics],
                "fault_codes": [f.__dict__ for f in fault_codes],
                "statistics": stats,
                "has_issues": any(m.status != "normal" for m in metrics) or len(fault_codes) > 0,
                "critical_count": sum(1 for m in metrics if m.status == "critical") + sum(1 for f in fault_codes if f.severity == "critical"),
                "warning_count": sum(1 for m in metrics if m.status == "warning") + sum(1 for f in fault_codes if f.severity == "warning"),
            }

            logger.info(f"Parsed {len(metrics)} metrics and {len(fault_codes)} fault codes")
            return result

        except Exception as e:
            logger.error(f"Error parsing OBD-II file: {e}")
            raise OBDParseError(f"Failed to parse OBD-II log: {str(e)}")

    def _find_valid_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Find valid OBD-II columns in the dataframe."""
        valid_columns = {}
        df_columns_lower = {col.lower(): col for col in df.columns}

        for metric_name, possible_names in self.COLUMN_MAPPINGS.items():
            for name in possible_names:
                if name.lower() in df_columns_lower:
                    valid_columns[metric_name] = df_columns_lower[name.lower()]
                    break

        return valid_columns

    def _extract_metrics(self, df: pd.DataFrame) -> List[OBDMetric]:
        """Extract and analyze metrics from the dataframe."""
        metrics = []
        column_map = self._find_valid_columns(df)

        # Metrics that should only be evaluated when engine is running
        engine_dependent_metrics = ["engine_rpm", "maf_rate", "engine_load"]

        # Get engine RPM column to filter engine-off rows
        rpm_column = column_map.get("engine_rpm")
        engine_running_mask = None
        if rpm_column is not None:
            rpm_values = pd.to_numeric(df[rpm_column], errors="coerce")
            # Engine is considered "running" when RPM > 100
            engine_running_mask = rpm_values > 100

        for metric_name, column_name in column_map.items():
            if metric_name in ["fault_codes", "timestamp"]:
                continue

            try:
                values = pd.to_numeric(df[column_name], errors="coerce").dropna()
                if values.empty:
                    continue

                # For engine-dependent metrics, only consider values when engine is running
                if metric_name in engine_dependent_metrics and engine_running_mask is not None:
                    running_values = values[engine_running_mask.reindex(values.index, fill_value=False)]
                    if not running_values.empty:
                        values = running_values

                # Calculate average value
                avg_value = values.mean()
                latest_value = values.iloc[-1] if len(values) > 0 else avg_value

                # Classify status
                status = self._classify_metric_status(metric_name, latest_value)

                # Get normal range string
                ranges = self.METRIC_RANGES.get(metric_name, {})
                normal_range = f"{ranges.get('min', 'N/A')} - {ranges.get('max', 'N/A')}" if ranges else "N/A"

                metric = OBDMetric(
                    name=metric_name,
                    value=float(round(latest_value, 2)),
                    unit=self.METRIC_UNITS.get(metric_name, ""),
                    status=status,
                    description=self.METRIC_DESCRIPTIONS.get(metric_name, ""),
                    normal_range=normal_range
                )
                metrics.append(metric)

            except Exception as e:
                logger.warning(f"Error extracting metric {metric_name}: {e}")

        return metrics

    def _extract_fault_codes(self, df: pd.DataFrame) -> List[FaultCode]:
        """Extract fault codes from the dataframe."""
        fault_codes = []
        column_map = self._find_valid_columns(df)

        if "fault_codes" not in column_map:
            return fault_codes

        dtc_column = column_map["fault_codes"]

        # Collect all unique fault codes
        all_codes = set()
        for value in df[dtc_column].dropna():
            # Parse fault codes (may be comma-separated or space-separated)
            codes = re.findall(r"[PCBU][0-9]{4}", str(value).upper())
            all_codes.update(codes)

        # Create FaultCode objects
        for code in sorted(all_codes):
            fault_code = self._create_fault_code(code)
            if fault_code:
                fault_codes.append(fault_code)

        return fault_codes

    def _create_fault_code(self, code: str) -> Optional[FaultCode]:
        """Create a FaultCode object from a code string."""
        code = code.upper()

        # Determine category
        prefix = code[0]
        categories = {
            "P": "powertrain",
            "C": "chassis",
            "B": "body",
            "U": "network"
        }
        category = categories.get(prefix, "unknown")

        # Check if generic (second character is 0) or manufacturer-specific
        is_generic = code[1] == "0" or code[1] == "2" or code[1] == "3"

        # Look up in database
        if code in self.FAULT_CODE_DATABASE:
            description, severity, causes = self.FAULT_CODE_DATABASE[code]
            return FaultCode(
                code=code,
                description=description,
                severity=severity,
                category=category,
                is_generic=is_generic,
                possible_causes=causes,
                recommended_action=self._get_recommended_action(severity)
            )
        else:
            # Unknown code
            return FaultCode(
                code=code,
                description=f"{'Generic' if is_generic else 'Manufacturer-specific'} {category} code",
                severity="warning" if is_generic else "info",
                category=category,
                is_generic=is_generic,
                possible_causes=["Refer to vehicle service manual"],
                recommended_action="Have the code diagnosed by a professional mechanic"
            )

    def _classify_metric_status(self, metric_name: str, value: float) -> str:
        """Classify a metric value as normal, warning, or critical."""
        ranges = self.METRIC_RANGES.get(metric_name)
        if not ranges:
            return "normal"

        # Critical range check
        if value < ranges.get("critical_low", float("-inf")) or value > ranges.get("critical_high", float("inf")):
            return "critical"

        # Warning range check
        if value < ranges.get("warning_low", float("-inf")) or value > ranges.get("warning_high", float("inf")):
            return "warning"

        # Normal range check
        if value < ranges.get("min", float("-inf")) or value > ranges.get("max", float("inf")):
            return "warning"

        return "normal"

    def _get_recommended_action(self, severity: str) -> str:
        """Get recommended action based on severity."""
        actions = {
            "critical": "Stop driving immediately and have the vehicle inspected by a professional mechanic.",
            "warning": "Schedule a service appointment soon to diagnose and address this issue.",
            "info": "Monitor the situation. This may not require immediate attention."
        }
        return actions.get(severity, "Consult a professional mechanic for diagnosis.")

    def _calculate_statistics(self, df: pd.DataFrame, metrics: List[OBDMetric]) -> Dict[str, Any]:
        """Calculate summary statistics for the OBD data."""
        stats = {
            "total_rows": len(df),
            "metrics_count": len(metrics),
            "normal_count": sum(1 for m in metrics if m.status == "normal"),
            "warning_count": sum(1 for m in metrics if m.status == "warning"),
            "critical_count": sum(1 for m in metrics if m.status == "critical"),
        }

        # Add per-metric statistics
        column_map = self._find_valid_columns(df)
        metric_stats = {}

        for metric in metrics:
            if metric.name in column_map:
                col = column_map[metric.name]
                values = pd.to_numeric(df[col], errors="coerce").dropna()
                if not values.empty:
                    metric_stats[metric.name] = {
                        "min": float(round(values.min(), 2)),
                        "max": float(round(values.max(), 2)),
                        "mean": float(round(values.mean(), 2)),
                        "std": float(round(values.std(), 2)) if len(values) > 1 else 0.0
                    }

        stats["metric_statistics"] = metric_stats
        return stats

    def get_metric_explanation(self, metric_name: str) -> str:
        """Get a human-readable explanation of a metric."""
        return self.METRIC_DESCRIPTIONS.get(metric_name, f"OBD-II metric: {metric_name}")

    def get_fault_code_info(self, code: str) -> Optional[FaultCode]:
        """Get information about a specific fault code."""
        return self._create_fault_code(code)
