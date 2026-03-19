#!/usr/bin/env python3
"""
Microphone Array Calibration Script.

Automatically calibrates a microphone array using various calibration
procedures. Supports both simulation and real hardware modes.

Usage:
    # Calibrate real hardware
    python calibrate_array.py --mode real --output calibration.json

    # Calibrate in simulation (for testing)
    python calibrate_array.py --mode sim --output calibration.json

    # Validate existing calibration
    python calibrate_array.py --validate calibration.json

    # List available procedures
    python calibrate_array.py --list-procedures
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from hal.factory import create_microphone_array, create_transducer
from hal.base import HardwareConfig, HardwareMode
from calibration.auto_calibrate import ArrayCalibrator, CalibrationResult
from calibration.uncertainty import CalibrationValidator, UncertaintyEstimator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Microphone Array Calibration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full calibration on real hardware
  %(prog)s --mode real --output calibration.json

  # Quick test calibration in simulation
  %(prog)s --mode sim --output test_cal.json --quick

  # Validate existing calibration
  %(prog)s --validate calibration.json

  # Generate calibration report
  %(prog)s --input calibration.json --report report.txt
        """,
    )
    
    parser.add_argument(
        "--mode",
        choices=["sim", "real", "hybrid"],
        default="sim",
        help="Operation mode (default: sim)",
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output calibration file",
    )
    
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        help="Input calibration file (for validation/report)",
    )
    
    parser.add_argument(
        "--validate",
        type=Path,
        metavar="CAL_FILE",
        help="Validate existing calibration file",
    )
    
    parser.add_argument(
        "--report",
        type=Path,
        metavar="REPORT_FILE",
        help="Generate calibration report",
    )
    
    parser.add_argument(
        "--list-procedures",
        action="store_true",
        help="List available calibration procedures",
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick calibration (fewer iterations)",
    )
    
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=48000,
        help="Sample rate in Hz (default: 48000)",
    )
    
    parser.add_argument(
        "--num-channels",
        type=int,
        default=4,
        help="Number of microphone channels (default: 4)",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    
    return parser.parse_args()


def list_procedures() -> None:
    """List available calibration procedures."""
    procedures = {
        "ToneCalibration": "Calibrate using known frequency tones (gain, phase)",
        "ImpulseCalibration": "Calibrate using impulse responses (time alignment)",
        "PositionCalibration": "Calibrate microphone positions (geometry)",
    }
    
    print("\nAvailable Calibration Procedures:")
    print("-" * 60)
    for name, description in procedures.items():
        print(f"  {name:25s} - {description}")
    print()


def run_calibration(
    mode: str,
    config: HardwareConfig,
    quick: bool = False,
) -> CalibrationResult:
    """
    Run full calibration procedure.
    
    Args:
        mode: Operation mode ("sim", "real", "hybrid")
        config: Hardware configuration
        quick: Use quick calibration
    
    Returns:
        Calibration result
    """
    logger.info(f"Starting calibration in {mode} mode")
    logger.info(f"Configuration: {config.num_channels}ch @ {config.sample_rate}Hz")
    
    # Create hardware components
    logger.info("Initializing hardware...")
    mics = create_microphone_array(mode, config)
    transducer = create_transducer(mode, config)
    
    # Create calibrator
    calibrator = ArrayCalibrator(mics, transducer)
    
    # Run calibration
    logger.info("Running calibration procedures...")
    result = calibrator.calibrate()
    
    # Cleanup
    mics.close()
    transducer.close()
    
    return result


def validate_calibration(cal_path: Path) -> dict[str, Any]:
    """
    Validate existing calibration.
    
    Args:
        cal_path: Path to calibration file
    
    Returns:
        Validation results
    """
    logger.info(f"Validating calibration: {cal_path}")
    
    # Load calibration
    from hal.base import CalibrationData
    calibration = CalibrationData.load(cal_path)
    
    # Validate
    validator = CalibrationValidator()
    results = validator.full_validation(calibration)
    
    return results


def generate_report(
    calibration: Any,
    validation: dict[str, Any] | None,
    output_path: Path,
) -> None:
    """
    Generate calibration report.
    
    Args:
        calibration: Calibration data
        validation: Validation results
        output_path: Output file path
    """
    logger.info(f"Generating report: {output_path}")
    
    with open(output_path, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("MICROPHONE ARRAY CALIBRATION REPORT\n")
        f.write("=" * 70 + "\n\n")
        
        # Calibration info
        f.write("CALIBRATION DATA\n")
        f.write("-" * 70 + "\n")
        f.write(f"Calibration Time: {calibration.calibration_time}\n")
        f.write(f"Quality Score: {calibration.quality_score:.3f}\n")
        f.write(f"Valid Temperature Range: {calibration.valid_temperature_range}\n")
        f.write("\n")
        
        # Gain calibration
        f.write("GAIN CALIBRATION\n")
        f.write("-" * 70 + "\n")
        for i, (gain, unc) in enumerate(zip(
            calibration.gain_calibration,
            calibration.gain_uncertainty,
        )):
            f.write(f"  Channel {i}: gain={gain:.4f} ± {unc:.4f}\n")
        f.write("\n")
        
        # Time calibration
        f.write("TIME OFFSET CALIBRATION\n")
        f.write("-" * 70 + "\n")
        for i, (offset, unc) in enumerate(zip(
            calibration.time_offset,
            calibration.time_uncertainty,
        )):
            f.write(f"  Channel {i}: offset={offset:.2e}s ± {unc:.2e}s\n")
        f.write("\n")
        
        # Position calibration
        f.write("MICROPHONE POSITIONS\n")
        f.write("-" * 70 + "\n")
        for i, (pos, unc) in enumerate(zip(
            calibration.microphone_positions,
            calibration.position_uncertainty,
        )):
            f.write(f"  Mic {i}: ({pos[0]:.4f}, {pos[1]:.4f}, {pos[2]:.4f}) m\n")
            f.write(f"         ± ({unc[0]:.4f}, {unc[1]:.4f}, {unc[2]:.4f}) m\n")
        f.write("\n")
        
        # Validation results
        if validation:
            f.write("VALIDATION RESULTS\n")
            f.write("-" * 70 + "\n")
            f.write(f"Overall Valid: {validation['valid']}\n")
            f.write(f"Overall Quality: {validation['overall_quality']:.3f}\n")
            f.write("\n")
            
            if "gain" in validation:
                f.write("Gain Validation:\n")
                f.write(f"  Valid: {validation['gain']['valid']}\n")
                f.write(f"  Relative Variation: {validation['gain']['relative_variation']:.4f}\n")
                f.write("\n")
            
            if "time" in validation:
                f.write("Time Validation:\n")
                f.write(f"  Valid: {validation['time']['valid']}\n")
                f.write(f"  Max Offset: {validation['time']['max_offset']:.2e}s\n")
                f.write("\n")
            
            if "position" in validation:
                f.write("Position Validation:\n")
                f.write(f"  Valid: {validation['position']['valid']}\n")
                f.write(f"  Mean Spacing: {validation['position']['mean_spacing']:.4f}m\n")
                f.write("\n")
            
            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 70 + "\n")
            for rec in validation.get("recommendations", []):
                f.write(f"  - {rec}\n")
            f.write("\n")
        
        f.write("=" * 70 + "\n")
        f.write("End of Report\n")
        f.write("=" * 70 + "\n")


def print_calibration_summary(result: CalibrationResult) -> None:
    """Print calibration summary to console."""
    print("\n" + "=" * 70)
    print("CALIBRATION SUMMARY")
    print("=" * 70)
    
    print(f"\nStatus: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Quality Score: {result.quality_score:.3f}")
    
    if result.error_message:
        print(f"Error: {result.error_message}")
    
    print("\nCalibration Parameters:")
    print(f"  Gain: {result.calibration.gain_calibration}")
    print(f"  Time Offsets: {result.calibration.time_offset}")
    
    print("\nUncertainty Estimates:")
    print(f"  Gain: ±{result.calibration.gain_uncertainty}")
    print(f"  Time: ±{result.calibration.time_uncertainty}")
    
    print("=" * 70 + "\n")


def print_validation_summary(results: dict[str, Any]) -> None:
    """Print validation summary to console."""
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    print(f"\nOverall Valid: {results['valid']}")
    print(f"Overall Quality: {results['overall_quality']:.3f}")
    
    print("\nRecommendations:")
    for rec in results.get("recommendations", []):
        print(f"  - {rec}")
    
    print("=" * 70 + "\n")


def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Set verbose logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # List procedures
    if args.list_procedures:
        list_procedures()
        return 0
    
    # Validate existing calibration
    if args.validate:
        if not args.validate.exists():
            logger.error(f"Calibration file not found: {args.validate}")
            return 1
        
        results = validate_calibration(args.validate)
        print_validation_summary(results)
        
        # Generate report if requested
        if args.report:
            from hal.base import CalibrationData
            cal = CalibrationData.load(args.validate)
            generate_report(cal, results, args.report)
        
        return 0 if results["valid"] else 1
    
    # Generate report from existing calibration
    if args.report and args.input:
        if not args.input.exists():
            logger.error(f"Input file not found: {args.input}")
            return 1
        
        from hal.base import CalibrationData
        cal = CalibrationData.load(args.input)
        
        # Validate if not already done
        validation = None
        if not args.validate:
            validator = CalibrationValidator()
            validation = validator.full_validation(cal)
        
        generate_report(cal, validation, args.report)
        return 0
    
    # Run calibration
    config = HardwareConfig(
        sample_rate=args.sample_rate,
        num_channels=args.num_channels,
    )
    
    result = run_calibration(args.mode, config, args.quick)
    
    # Print summary
    print_calibration_summary(result)
    
    # Save calibration
    if args.output:
        if result.success:
            result.calibration.save(args.output)
            logger.info(f"Calibration saved to: {args.output}")
        else:
            logger.warning("Calibration failed - not saving")
    
    # Generate report
    if args.report:
        validator = CalibrationValidator()
        validation = validator.full_validation(result.calibration)
        generate_report(result.calibration, validation, args.report)
    
    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
