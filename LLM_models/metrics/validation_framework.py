"""
Human Effort Validation Framework

This module provides tools for validating computational-to-human effort mappings
through empirical studies, expert assessment, and iterative calibration.
"""

import json
import statistics
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import csv

@dataclass
class EmpiricalObservation:
    """Records actual human performance on a task"""
    participant_id: str
    task_description: str
    expertise_level: str
    actual_time_minutes: float
    errors_made: int
    completion_quality: float  # 0-1 scale
    self_reported_difficulty: int  # 1-10 scale
    self_reported_confidence: float  # 0-1 scale
    strategy_used: str
    external_resources_used: List[str]
    fatigue_level_start: int  # 1-10
    fatigue_level_end: int  # 1-10
    notes: str
    timestamp: datetime
    
    # Task-specific metrics matching your domain
    classes_correctly_identified: int = 0
    properties_correctly_identified: int = 0
    inheritance_relationships_correct: int = 0
    false_positives: int = 0
    false_negatives: int = 0

@dataclass
class ValidationStudyDesign:
    """Defines parameters for a human performance validation study"""
    study_name: str
    target_tasks: List[str]  # Task types to validate
    participant_criteria: Dict[str, Any]  # Required expertise, background
    task_complexity_range: Tuple[float, float]  # Min/max complexity scores
    sample_size_target: int
    time_limit_minutes: Optional[float]
    controlled_variables: List[str]  # What to keep constant
    measured_variables: List[str]  # What to measure
    
class ValidationFramework:
    """Framework for validating human effort estimates"""
    
    def __init__(self):
        self.empirical_data: List[EmpiricalObservation] = []
        self.calibration_factors: Dict[str, float] = {}
        self.validation_studies: List[ValidationStudyDesign] = []
        
    def design_validation_study(self, task_type: str, complexity_levels: List[float]) -> ValidationStudyDesign:
        """Design a validation study for specific task types"""
        
        study = ValidationStudyDesign(
            study_name=f"validation_{task_type}_{datetime.now().strftime('%Y%m%d')}",
            target_tasks=[task_type],
            participant_criteria={
                "min_ontology_experience_months": 6,
                "programming_background": True,
                "semantic_web_familiarity": "basic"
            },
            task_complexity_range=(min(complexity_levels), max(complexity_levels)),
            sample_size_target=12,  # Minimum for statistical significance
            time_limit_minutes=120,  # 2 hours max per session
            controlled_variables=[
                "task_instructions", 
                "available_tools", 
                "environment_setup",
                "ontology_documentation"
            ],
            measured_variables=[
                "completion_time",
                "accuracy",
                "strategy_changes", 
                "external_lookups",
                "error_recovery_time",
                "cognitive_load_indicators"
            ]
        )
        
        self.validation_studies.append(study)
        return study
    
    def collect_empirical_observation(self, observation: EmpiricalObservation):
        """Add an empirical observation to the dataset"""
        self.empirical_data.append(observation)
    
    def analyze_prediction_accuracy(self, task_type: str = None) -> Dict[str, Any]:
        """Analyze how well predictions match empirical observations"""
        
        relevant_observations = self.empirical_data
        if task_type:
            relevant_observations = [obs for obs in self.empirical_data 
                                   if task_type in obs.task_description]
        
        if not relevant_observations:
            return {"error": "No empirical data available"}
        
        # Compare predicted vs actual times
        time_errors = []
        difficulty_correlations = []
        quality_vs_time = []
        
        for obs in relevant_observations:
            # Would need to re-run prediction for this specific task
            # This is a placeholder for the comparison logic
            predicted_time = self._get_predicted_time_for_observation(obs)
            if predicted_time:
                error_percentage = abs(predicted_time - obs.actual_time_minutes) / obs.actual_time_minutes
                time_errors.append(error_percentage)
            
            difficulty_correlations.append({
                "self_reported": obs.self_reported_difficulty,
                "actual_time": obs.actual_time_minutes,
                "errors": obs.errors_made
            })
            
            quality_vs_time.append({
                "time": obs.actual_time_minutes,
                "quality": obs.completion_quality,
                "expertise": obs.expertise_level
            })
        
        analysis = {
            "sample_size": len(relevant_observations),
            "time_prediction_accuracy": {
                "mean_error_percentage": statistics.mean(time_errors) if time_errors else None,
                "median_error_percentage": statistics.median(time_errors) if time_errors else None,
                "std_dev": statistics.stdev(time_errors) if len(time_errors) > 1 else None
            },
            "expertise_impact": self._analyze_expertise_impact(relevant_observations),
            "strategy_effectiveness": self._analyze_strategy_effectiveness(relevant_observations),
            "error_patterns": self._analyze_error_patterns(relevant_observations),
            "fatigue_effects": self._analyze_fatigue_effects(relevant_observations)
        }
        
        return analysis
    
    def _get_predicted_time_for_observation(self, obs: EmpiricalObservation) -> Optional[float]:
        """Get predicted time for a specific observation (placeholder)"""
        # This would integrate with your main prediction system
        return None
    
    def _analyze_expertise_impact(self, observations: List[EmpiricalObservation]) -> Dict[str, Any]:
        """Analyze how expertise level affects performance"""
        
        by_expertise = {}
        for obs in observations:
            if obs.expertise_level not in by_expertise:
                by_expertise[obs.expertise_level] = []
            by_expertise[obs.expertise_level].append(obs)
        
        expertise_analysis = {}
        for level, obs_list in by_expertise.items():
            if obs_list:
                expertise_analysis[level] = {
                    "avg_time": statistics.mean([obs.actual_time_minutes for obs in obs_list]),
                    "avg_quality": statistics.mean([obs.completion_quality for obs in obs_list]),
                    "avg_errors": statistics.mean([obs.errors_made for obs in obs_list]),
                    "sample_size": len(obs_list)
                }
        
        return expertise_analysis
    
    def _analyze_strategy_effectiveness(self, observations: List[EmpiricalObservation]) -> Dict[str, Any]:
        """Analyze which strategies work best"""
        
        by_strategy = {}
        for obs in observations:
            if obs.strategy_used not in by_strategy:
                by_strategy[obs.strategy_used] = []
            by_strategy[obs.strategy_used].append(obs)
        
        strategy_analysis = {}
        for strategy, obs_list in by_strategy.items():
            if obs_list:
                strategy_analysis[strategy] = {
                    "avg_time": statistics.mean([obs.actual_time_minutes for obs in obs_list]),
                    "avg_quality": statistics.mean([obs.completion_quality for obs in obs_list]),
                    "success_rate": len([obs for obs in obs_list if obs.completion_quality > 0.8]) / len(obs_list),
                    "sample_size": len(obs_list)
                }
        
        return strategy_analysis
    
    def _analyze_error_patterns(self, observations: List[EmpiricalObservation]) -> Dict[str, Any]:
        """Analyze common error patterns"""
        
        error_analysis = {
            "high_error_tasks": [],
            "error_vs_time_correlation": 0.0,
            "common_error_types": {},
            "error_recovery_patterns": []
        }
        
        # Find tasks with high error rates
        for obs in observations:
            if obs.errors_made > 2:  # Threshold for "high error"
                error_analysis["high_error_tasks"].append({
                    "task": obs.task_description,
                    "errors": obs.errors_made,
                    "time": obs.actual_time_minutes,
                    "expertise": obs.expertise_level
                })
        
        # Calculate correlation between errors and time
        if len(observations) > 1:
            times = [obs.actual_time_minutes for obs in observations]
            errors = [obs.errors_made for obs in observations]
            correlation = self._calculate_correlation(times, errors)
            error_analysis["error_vs_time_correlation"] = correlation
        
        return error_analysis
    
    def _analyze_fatigue_effects(self, observations: List[EmpiricalObservation]) -> Dict[str, Any]:
        """Analyze how fatigue affects performance"""
        
        fatigue_data = []
        for obs in observations:
            fatigue_increase = obs.fatigue_level_end - obs.fatigue_level_start
            fatigue_data.append({
                "fatigue_increase": fatigue_increase,
                "time": obs.actual_time_minutes,
                "quality": obs.completion_quality,
                "errors": obs.errors_made
            })
        
        return {
            "avg_fatigue_increase": statistics.mean([d["fatigue_increase"] for d in fatigue_data]),
            "fatigue_vs_quality_correlation": self._calculate_correlation(
                [d["fatigue_increase"] for d in fatigue_data],
                [d["quality"] for d in fatigue_data]
            ),
            "fatigue_vs_time_correlation": self._calculate_correlation(
                [d["fatigue_increase"] for d in fatigue_data], 
                [d["time"] for d in fatigue_data]
            )
        }
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def calibrate_model(self, task_type: str = None) -> Dict[str, float]:
        """Calibrate the prediction model based on empirical data"""
        
        analysis = self.analyze_prediction_accuracy(task_type)
        
        # Calculate calibration factors based on systematic biases
        calibration_factors = {}
        
        if analysis.get("time_prediction_accuracy"):
            mean_error = analysis["time_prediction_accuracy"].get("mean_error_percentage", 0)
            if mean_error > 0.1:  # If consistently off by more than 10%
                calibration_factors["time_multiplier"] = 1 + mean_error
        
        # Expertise-based calibrations
        expertise_analysis = analysis.get("expertise_impact", {})
        for expertise_level, data in expertise_analysis.items():
            if data["sample_size"] >= 3:  # Minimum sample for calibration
                key = f"{expertise_level}_time_factor"
                # Calculate factor based on observed vs expected performance
                calibration_factors[key] = data["avg_time"] / 30.0  # Placeholder baseline
        
        self.calibration_factors.update(calibration_factors)
        return calibration_factors
    
    def export_study_template(self, study_design: ValidationStudyDesign, filepath: str):
        """Export a template for conducting the validation study"""
        
        template = {
            "study_metadata": asdict(study_design),
            "data_collection_form": {
                "participant_demographics": {
                    "id": "",
                    "expertise_level": ["novice", "intermediate", "expert"], 
                    "years_experience_ontologies": 0,
                    "years_experience_programming": 0,
                    "semantic_web_background": ["none", "basic", "intermediate", "advanced"]
                },
                "pre_task": {
                    "fatigue_level": "1-10 scale",
                    "confidence_level": "1-10 scale", 
                    "time_available": "minutes"
                },
                "task_execution": {
                    "start_time": "timestamp",
                    "strategy_notes": "free text",
                    "external_resources": "list of resources consulted",
                    "decision_points": "key decisions made",
                    "difficulty_moments": "when task became challenging"
                },
                "post_task": {
                    "end_time": "timestamp",
                    "fatigue_level": "1-10 scale",
                    "confidence_in_result": "1-10 scale",
                    "perceived_difficulty": "1-10 scale",
                    "strategy_effectiveness": "1-10 scale",
                    "what_would_help": "free text"
                },
                "result_validation": {
                    "correct_classes_identified": 0,
                    "incorrect_classes_identified": 0,
                    "correct_properties_identified": 0,
                    "incorrect_properties_identified": 0,
                    "correct_inheritance_relationships": 0,
                    "missed_relationships": 0,
                    "overall_quality_score": "0-1 scale"
                }
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(template, f, indent=2, default=str)
    
    def import_empirical_data(self, csv_filepath: str):
        """Import empirical data from CSV file"""
        
        with open(csv_filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                observation = EmpiricalObservation(
                    participant_id=row['participant_id'],
                    task_description=row['task_description'],
                    expertise_level=row['expertise_level'],
                    actual_time_minutes=float(row['actual_time_minutes']),
                    errors_made=int(row['errors_made']),
                    completion_quality=float(row['completion_quality']),
                    self_reported_difficulty=int(row['self_reported_difficulty']),
                    self_reported_confidence=float(row['self_reported_confidence']),
                    strategy_used=row['strategy_used'],
                    external_resources_used=row['external_resources_used'].split(',') if row['external_resources_used'] else [],
                    fatigue_level_start=int(row['fatigue_level_start']),
                    fatigue_level_end=int(row['fatigue_level_end']),
                    notes=row['notes'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    classes_correctly_identified=int(row.get('classes_correctly_identified', 0)),
                    properties_correctly_identified=int(row.get('properties_correctly_identified', 0)),
                    inheritance_relationships_correct=int(row.get('inheritance_relationships_correct', 0)),
                    false_positives=int(row.get('false_positives', 0)),
                    false_negatives=int(row.get('false_negatives', 0))
                )
                self.collect_empirical_observation(observation)


class AdaptiveCalibration:
    """Continuously adapts predictions based on new empirical data"""
    
    def __init__(self, validation_framework: ValidationFramework):
        self.validation_framework = validation_framework
        self.learning_rate = 0.1
        self.confidence_threshold = 0.8
        
    def update_predictions(self, new_observations: List[EmpiricalObservation]):
        """Update prediction models based on new observations"""
        
        for obs in new_observations:
            self.validation_framework.collect_empirical_observation(obs)
        
        # Recalibrate with updated data
        new_factors = self.validation_framework.calibrate_model()
        
        # Gradually adjust existing factors
        for factor_name, new_value in new_factors.items():
            if factor_name in self.validation_framework.calibration_factors:
                old_value = self.validation_framework.calibration_factors[factor_name]
                adjusted_value = old_value + self.learning_rate * (new_value - old_value)
                self.validation_framework.calibration_factors[factor_name] = adjusted_value
            else:
                self.validation_framework.calibration_factors[factor_name] = new_value
    
    def get_confidence_intervals(self, predicted_time: float, task_complexity: float, 
                               expertise_level: str) -> Tuple[float, float]:
        """Calculate confidence intervals for predictions"""
        
        # Find similar historical observations
        similar_observations = []
        for obs in self.validation_framework.empirical_data:
            if (obs.expertise_level == expertise_level and 
                abs(obs.actual_time_minutes - predicted_time) < predicted_time * 0.5):
                similar_observations.append(obs)
        
        if len(similar_observations) < 3:
            # Not enough data - use wide confidence interval
            return (predicted_time * 0.5, predicted_time * 2.0)
        
        # Calculate empirical confidence interval
        times = [obs.actual_time_minutes for obs in similar_observations]
        std_dev = statistics.stdev(times)
        mean_time = statistics.mean(times)
        
        # 95% confidence interval (assuming normal distribution)
        margin = 1.96 * std_dev
        return (max(0, mean_time - margin), mean_time + margin)
