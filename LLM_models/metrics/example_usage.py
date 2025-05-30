"""
Example usage of the human effort estimation and validation framework.

This script demonstrates how to:
1. Use the advanced cognition modeling for realistic estimates
2. Set up validation studies 
3. Calibrate predictions based on empirical data
4. Handle the fundamental differences between human and computational approaches
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from python_metrics import TaskMetrics, AdvancedEffortMapper
from validation_framework import ValidationFramework, EmpiricalObservation, AdaptiveCalibration
from datetime import datetime
import json

def demonstrate_realistic_estimation():
    """Show how to get realistic human effort estimates"""
    
    # Sample computational metrics from your ontology analysis
    sample_metrics = TaskMetrics(
        task_name="find_value_properties_temperature_sensor",
        execution_time=0.23,  # seconds
        memory_peak=15.2,     # MB
        graph_queries=45,
        classes_analyzed=8,
        properties_found=12,
        inheritance_levels=4,
        complexity_score=18.5
    )
    
    mapper = AdvancedEffortMapper()
    
    print("=== Human vs Computational Effort Analysis ===\n")
    
    # Compare different human approaches
    comparison = mapper.compare_human_vs_computational(sample_metrics)
    
    print(f"Computational baseline:")
    print(f"  Time: {comparison['computational_baseline']['time_seconds']:.2f} seconds")
    print(f"  Memory: {comparison['computational_baseline']['memory_mb']:.1f} MB")
    print(f"  Accuracy: {comparison['computational_baseline']['accuracy']:.1%}")
    
    print(f"\nHuman estimates:")
    for approach, results in comparison['human_estimates'].items():
        profile, strategy = approach.split('_', 1)
        print(f"\n{profile.title()} using {strategy.replace('_', ' ')} approach:")
        print(f"  Estimated time: {results['estimated_time_minutes']:.1f} minutes")
        print(f"  vs Computer: {results['time_vs_computer']:.0f}x slower")
        print(f"  Cognitive load: {results['cognitive_load']:.1f}/10")
        print(f"  Error probability: {results['error_probability']:.1%}")
        print(f"  Result confidence: {results['result_confidence']:.1%}")
        
        # Show human-specific factors
        factors = results['human_vs_computer_factors']
        print(f"  Human-specific challenges:")
        print(f"    Sequential processing penalty: {factors['sequential_processing_penalty']:.1f}x")
        print(f"    Working memory limit: {factors['working_memory_constraint']} concepts")
        print(f"    Context switches needed: {factors['context_switching_overhead']}")
        print(f"    External lookups required: {factors['external_dependencies']}")

def demonstrate_validation_study_setup():
    """Show how to set up a validation study"""
    
    validation = ValidationFramework()
    
    # Design a study for your specific task types
    study = validation.design_validation_study(
        task_type="ontology_value_property_identification",
        complexity_levels=[5.0, 10.0, 15.0, 20.0, 25.0]
    )
    
    print("\n=== Validation Study Design ===\n")
    print(f"Study: {study.study_name}")
    print(f"Target sample size: {study.sample_size_target} participants")
    print(f"Complexity range: {study.task_complexity_range}")
    print(f"Time limit: {study.time_limit_minutes} minutes")
    
    # Export study template
    template_path = "validation_study_template.json"
    validation.export_study_template(study, template_path)
    print(f"Study template exported to: {template_path}")
    
    return validation

def simulate_empirical_data_collection(validation: ValidationFramework):
    """Simulate collecting some empirical observations"""
    
    print("\n=== Simulated Empirical Data Collection ===\n")
    
    # Simulate some observations (in real use, this would be actual human data)
    observations = [
        EmpiricalObservation(
            participant_id="P001",
            task_description="find_value_properties_temperature_sensor",
            expertise_level="intermediate",
            actual_time_minutes=35.5,
            errors_made=2,
            completion_quality=0.85,
            self_reported_difficulty=6,
            self_reported_confidence=0.75,
            strategy_used="systematic_comprehensive",
            external_resources_used=["ontology_documentation", "web_search"],
            fatigue_level_start=3,
            fatigue_level_end=6,
            notes="Struggled with inheritance relationships",
            timestamp=datetime.now(),
            classes_correctly_identified=6,
            properties_correctly_identified=10,
            inheritance_relationships_correct=3,
            false_positives=2,
            false_negatives=1
        ),
        EmpiricalObservation(
            participant_id="P002", 
            task_description="find_value_properties_temperature_sensor",
            expertise_level="expert",
            actual_time_minutes=18.2,
            errors_made=0,
            completion_quality=0.95,
            self_reported_difficulty=4,
            self_reported_confidence=0.9,
            strategy_used="expert_intuitive",
            external_resources_used=[],
            fatigue_level_start=2,
            fatigue_level_end=3,
            notes="Used domain knowledge shortcuts",
            timestamp=datetime.now(),
            classes_correctly_identified=8,
            properties_correctly_identified=12,
            inheritance_relationships_correct=4,
            false_positives=0,
            false_negatives=0
        ),
        EmpiricalObservation(
            participant_id="P003",
            task_description="find_value_properties_temperature_sensor", 
            expertise_level="novice",
            actual_time_minutes=78.3,
            errors_made=5,
            completion_quality=0.65,
            self_reported_difficulty=9,
            self_reported_confidence=0.4,
            strategy_used="pragmatic_selective",
            external_resources_used=["ontology_documentation", "web_search", "colleague_consultation"],
            fatigue_level_start=2,
            fatigue_level_end=8,
            notes="Overwhelmed by inheritance complexity",
            timestamp=datetime.now(),
            classes_correctly_identified=5,
            properties_correctly_identified=7,
            inheritance_relationships_correct=1,
            false_positives=4,
            false_negatives=3
        )
    ]
    
    for obs in observations:
        validation.collect_empirical_observation(obs)
        print(f"Collected data from {obs.participant_id} ({obs.expertise_level}): "
              f"{obs.actual_time_minutes:.1f} min, quality: {obs.completion_quality:.1%}")

def analyze_and_calibrate(validation: ValidationFramework):
    """Analyze the empirical data and calibrate the model"""
    
    print("\n=== Analysis and Calibration ===\n")
    
    # Analyze prediction accuracy
    analysis = validation.analyze_prediction_accuracy("find_value_properties")
    
    print(f"Sample size: {analysis['sample_size']}")
    
    if analysis.get('expertise_impact'):
        print("\nExpertise Impact Analysis:")
        for level, data in analysis['expertise_impact'].items():
            print(f"  {level.title()}:")
            print(f"    Average time: {data['avg_time']:.1f} minutes")
            print(f"    Average quality: {data['avg_quality']:.1%}")
            print(f"    Average errors: {data['avg_errors']:.1f}")
    
    if analysis.get('strategy_effectiveness'):
        print("\nStrategy Effectiveness Analysis:")
        for strategy, data in analysis['strategy_effectiveness'].items():
            print(f"  {strategy.replace('_', ' ').title()}:")
            print(f"    Average time: {data['avg_time']:.1f} minutes")
            print(f"    Success rate: {data['success_rate']:.1%}")
    
    # Calibrate the model
    calibration_factors = validation.calibrate_model()
    print(f"\nCalibration factors: {calibration_factors}")
    
    return analysis

def demonstrate_adaptive_calibration(validation: ValidationFramework):
    """Show how the system adapts with new data"""
    
    print("\n=== Adaptive Calibration ===\n")
    
    adaptive = AdaptiveCalibration(validation)
    
    # Simulate getting new observations
    new_observation = EmpiricalObservation(
        participant_id="P004",
        task_description="find_value_properties_co2_sensor",
        expertise_level="intermediate", 
        actual_time_minutes=42.1,
        errors_made=1,
        completion_quality=0.88,
        self_reported_difficulty=5,
        self_reported_confidence=0.8,
        strategy_used="pragmatic_selective",
        external_resources_used=["ontology_documentation"],
        fatigue_level_start=3,
        fatigue_level_end=5,
        notes="Similar to previous task but with different sensor type",
        timestamp=datetime.now(),
        classes_correctly_identified=7,
        properties_correctly_identified=11,
        inheritance_relationships_correct=3,
        false_positives=1,
        false_negatives=1
    )
    
    print("Updating model with new observation...")
    adaptive.update_predictions([new_observation])
    
    # Show confidence intervals for predictions
    predicted_time = 35.0  # Example prediction
    task_complexity = 15.0
    expertise = "intermediate"
    
    ci_low, ci_high = adaptive.get_confidence_intervals(predicted_time, task_complexity, expertise)
    print(f"Prediction: {predicted_time:.1f} minutes")
    print(f"95% confidence interval: [{ci_low:.1f}, {ci_high:.1f}] minutes")

def key_insights_for_research():
    """Provide insights on addressing human vs computational differences"""
    
    print("\n=== Key Insights for Handling Human-Computer Differences ===\n")
    
    insights = {
        "Cognitive Architecture Differences": [
            "Humans process sequentially, computers process in parallel",
            "Working memory limitations (7±2 items) vs unlimited computational memory", 
            "Fatigue accumulation vs consistent computational performance",
            "Context switching penalties vs seamless task switching"
        ],
        
        "Strategic Approach Differences": [
            "Humans use satisficing (good enough) vs computational optimization",
            "Heuristics and shortcuts vs exhaustive search",
            "Analogical reasoning vs logical inference",
            "Iterative refinement vs single-pass processing"
        ],
        
        "Validation Strategies": [
            "Use multiple human profiles (novice/intermediate/expert)",
            "Test different strategy approaches (comprehensive/selective/intuitive)",
            "Measure both time and quality outcomes",
            "Account for individual variation with confidence intervals",
            "Calibrate continuously with new empirical data"
        ],
        
        "Accuracy Considerations": [
            "Model cognitive constraints explicitly (working memory, attention)",
            "Include error recovery time and backtracking",
            "Factor in external dependency time (lookups, consultations)", 
            "Account for expertise-dependent shortcuts and domain knowledge",
            "Consider fatigue effects on longer tasks"
        ]
    }
    
    for category, points in insights.items():
        print(f"{category}:")
        for point in points:
            print(f"  • {point}")
        print()

if __name__ == "__main__":
    # Run the complete demonstration
    demonstrate_realistic_estimation()
    validation = demonstrate_validation_study_setup()
    simulate_empirical_data_collection(validation)
    analyze_and_calibrate(validation)
    demonstrate_adaptive_calibration(validation)
    key_insights_for_research()
    
    print("\n=== Summary ===")
    print("This framework addresses human-computer differences by:")
    print("1. Modeling human cognitive constraints explicitly")
    print("2. Using empirical validation to calibrate predictions") 
    print("3. Accounting for different expertise levels and strategies")
    print("4. Providing confidence intervals for predictions")
    print("5. Adapting continuously based on new observations")
