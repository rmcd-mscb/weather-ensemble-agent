# src/weather_agent/tools/statistics.py
"""Statistical analysis tools for ensemble forecasts"""

import json
import statistics
from typing import Any


def calculate_ensemble_statistics(
    forecast_data: dict[str, Any], variable: str = "temperature"
) -> dict:
    """
    Calculate ensemble statistics for a given weather variable across models.

    Args:
        forecast_data: Dictionary containing forecast data from multiple models
        variable: Which variable to analyze - 'temperature', 'precipitation', or 'wind_speed'

    Returns:
        Dict containing ensemble mean, spread, min, max, and percentiles for each time step
    """
    # Parse the forecast data if it's a JSON string
    if isinstance(forecast_data, str):
        try:
            forecast_data = json.loads(forecast_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for forecast_data"}

    # Extract valid models (those without errors)
    valid_models = {}
    for model_name, model_data in forecast_data.items():
        if isinstance(model_data, dict) and "error" not in model_data:
            valid_models[model_name] = model_data

    if not valid_models:
        return {"error": "No valid model data available"}

    # Get the variable data from each model
    model_values = {}
    times = None

    for model_name, model_data in valid_models.items():
        if variable in model_data:
            model_values[model_name] = model_data[variable]
            if times is None:
                times = model_data.get("times", [])

    if not model_values:
        return {"error": f"Variable '{variable}' not found in model data"}

    # Ensure all models have the same number of time steps
    num_timesteps = len(list(model_values.values())[0])
    for model_name, values in model_values.items():
        if len(values) != num_timesteps:
            return {"error": f"Model {model_name} has inconsistent number of timesteps"}

    # Calculate statistics for each time step
    ensemble_stats = {
        "variable": variable,
        "num_models": len(model_values),
        "models": list(model_values.keys()),
        "times": times,
        "ensemble_mean": [],
        "ensemble_median": [],
        "ensemble_std": [],
        "ensemble_min": [],
        "ensemble_max": [],
        "percentile_25": [],
        "percentile_75": [],
        "spread": [],  # max - min
    }

    for i in range(num_timesteps):
        # Get values from all models for this timestep
        values_at_time = [model_values[model][i] for model in model_values.keys()]

        # Calculate statistics
        ensemble_stats["ensemble_mean"].append(round(statistics.mean(values_at_time), 2))
        ensemble_stats["ensemble_median"].append(round(statistics.median(values_at_time), 2))
        ensemble_stats["ensemble_std"].append(
            round(statistics.stdev(values_at_time), 2) if len(values_at_time) > 1 else 0
        )
        ensemble_stats["ensemble_min"].append(round(min(values_at_time), 2))
        ensemble_stats["ensemble_max"].append(round(max(values_at_time), 2))

        # Calculate percentiles
        ensemble_stats["percentile_25"].append(
            round(statistics.quantiles(values_at_time, n=4)[0], 2)
        )
        ensemble_stats["percentile_75"].append(
            round(statistics.quantiles(values_at_time, n=4)[2], 2)
        )

        # Spread (range)
        ensemble_stats["spread"].append(round(max(values_at_time) - min(values_at_time), 2))

    return ensemble_stats


def calculate_model_agreement(
    forecast_data: dict[str, Any], variable: str = "temperature", threshold: float = 5.0
) -> dict:
    """
    Calculate how much models agree with each other for a given variable.

    Args:
        forecast_data: Dictionary containing forecast data from multiple models
        variable: Which variable to analyze
        threshold: Agreement threshold (e.g., models agree if within this value)

    Returns:
        Dict with agreement metrics
    """
    # Parse the forecast data if it's a JSON string
    if isinstance(forecast_data, str):
        try:
            forecast_data = json.loads(forecast_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for forecast_data"}

    # Extract valid models
    valid_models = {}
    for model_name, model_data in forecast_data.items():
        if isinstance(model_data, dict) and "error" not in model_data and variable in model_data:
            valid_models[model_name] = model_data[variable]

    if len(valid_models) < 2:
        return {"error": "Need at least 2 models to calculate agreement"}

    num_timesteps = len(list(valid_models.values())[0])
    times = list(forecast_data.values())[0].get("times", [])

    agreement_scores = []
    high_agreement_periods = []
    low_agreement_periods = []

    for i in range(num_timesteps):
        values_at_time = [valid_models[model][i] for model in valid_models.keys()]
        spread = max(values_at_time) - min(values_at_time)

        # Agreement score: 1.0 = perfect agreement, 0.0 = maximum disagreement
        # Normalize by threshold
        agreement_score = max(0.0, 1.0 - (spread / (threshold * 2)))
        agreement_scores.append(round(agreement_score, 3))

        # Track high and low agreement periods
        if agreement_score >= 0.8:
            high_agreement_periods.append(
                {
                    "time": times[i] if i < len(times) else f"timestep_{i}",
                    "spread": round(spread, 2),
                    "agreement_score": round(agreement_score, 3),
                }
            )
        elif agreement_score <= 0.5:
            low_agreement_periods.append(
                {
                    "time": times[i] if i < len(times) else f"timestep_{i}",
                    "spread": round(spread, 2),
                    "agreement_score": round(agreement_score, 3),
                }
            )

    return {
        "variable": variable,
        "num_models": len(valid_models),
        "models": list(valid_models.keys()),
        "threshold": threshold,
        "mean_agreement_score": round(statistics.mean(agreement_scores), 3),
        "min_agreement_score": round(min(agreement_scores), 3),
        "max_agreement_score": round(max(agreement_scores), 3),
        "agreement_scores": agreement_scores,
        "high_agreement_periods": high_agreement_periods[:10],  # Limit to first 10
        "low_agreement_periods": low_agreement_periods[:10],  # Limit to first 10
    }


def summarize_forecast_uncertainty(forecast_data: dict[str, Any]) -> dict:
    """
    Provide a high-level summary of forecast uncertainty across all variables.

    Args:
        forecast_data: Dictionary containing forecast data from multiple models

    Returns:
        Dict with overall uncertainty summary for all weather variables
    """
    # Parse the forecast data if it's a JSON string
    if isinstance(forecast_data, str):
        try:
            forecast_data = json.loads(forecast_data)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON format for forecast_data"}

    summary = {}

    for variable in ["temperature", "precipitation", "wind_speed"]:
        stats = calculate_ensemble_statistics(forecast_data, variable)

        if "error" in stats:
            summary[variable] = {"error": stats["error"]}
            continue

        # Calculate average spread and std dev across all timesteps
        avg_spread = round(statistics.mean(stats["spread"]), 2)
        avg_std = round(statistics.mean(stats["ensemble_std"]), 2)
        max_spread = round(max(stats["spread"]), 2)

        # Categorize uncertainty
        if variable == "temperature":
            if avg_spread < 3:
                uncertainty = "Low"
            elif avg_spread < 7:
                uncertainty = "Moderate"
            else:
                uncertainty = "High"
        elif variable == "precipitation":
            if avg_spread < 0.1:
                uncertainty = "Low"
            elif avg_spread < 0.3:
                uncertainty = "Moderate"
            else:
                uncertainty = "High"
        else:  # wind_speed
            if avg_spread < 5:
                uncertainty = "Low"
            elif avg_spread < 10:
                uncertainty = "Moderate"
            else:
                uncertainty = "High"

        summary[variable] = {
            "num_models": stats["num_models"],
            "average_spread": avg_spread,
            "max_spread": max_spread,
            "average_std_dev": avg_std,
            "uncertainty_level": uncertainty,
        }

    return summary
