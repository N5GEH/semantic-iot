import time
import tracemalloc
from functools import wraps
from dataclasses import dataclass
from typing import Dict, List, Any

@dataclass
class TaskMetrics:
    task_name: str
    execution_time: float
    memory_peak: float
    graph_queries: int
    classes_analyzed: int
    properties_found: int
    inheritance_levels: int
    complexity_score: float

def measure_effort(task_name: str):
    """Decorator to measure computational effort for a task"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Start measurements
            tracemalloc.start()
            start_time = time.time()
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Collect metrics
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Calculate complexity metrics from result
            metrics = TaskMetrics(
                task_name=task_name,
                execution_time=end_time - start_time,
                memory_peak=peak / 1024 / 1024,  # MB
                graph_queries=getattr(wrapper, '_query_count', 0),
                classes_analyzed=len(result) if isinstance(result, list) else 1,
                properties_found=sum(1 for item in result if item.get('property')) if isinstance(result, list) else 0,
                inheritance_levels=max((item.get('inheritance_level', 0) or 0 for item in result), default=0) if isinstance(result, list) else 0,
                complexity_score=calculate_complexity_score(result)
            )
            
            return result, metrics
        
        wrapper._query_count = 0
        return wrapper
    return decorator

def calculate_complexity_score(result):
    """Calculate a complexity score based on task results"""
    if not isinstance(result, list):
        return 1.0
    
    # Factor in number of items, inheritance depth, property types
    base_score = len(result)
    inheritance_penalty = sum(item.get('inheritance_level', 0) or 0 for item in result) * 0.5
    type_diversity = len(set(item.get('type', '') for item in result)) * 2
    
    return base_score + inheritance_penalty + type_diversity


from enum import Enum
from dataclasses import dataclass
from typing import Dict, List

class CognitiveTask(Enum):
    READING_COMPREHENSION = "reading_comprehension"
    PATTERN_MATCHING = "pattern_matching"
    LOGICAL_REASONING = "logical_reasoning"
    DOMAIN_KNOWLEDGE_RECALL = "domain_knowledge_recall"
    DECISION_MAKING = "decision_making"

@dataclass
class HumanEffortEstimate:
    task_name: str
    estimated_time_minutes: float
    cognitive_load: float  # 1-10 scale
    error_probability: float  # 0-1
    required_expertise: str  # novice, intermediate, expert
    cognitive_tasks: List[CognitiveTask]

class EffortMapper:
    def __init__(self):
        # Base time estimates for cognitive tasks (minutes)
        self.cognitive_task_times = {
            CognitiveTask.READING_COMPREHENSION: 0.5,  # per concept
            CognitiveTask.PATTERN_MATCHING: 1.0,       # per comparison
            CognitiveTask.LOGICAL_REASONING: 2.0,      # per inference step
            CognitiveTask.DOMAIN_KNOWLEDGE_RECALL: 0.3, # per fact lookup
            CognitiveTask.DECISION_MAKING: 1.5         # per decision point
        }
        
        # Complexity multipliers
        self.complexity_multipliers = {
            "inheritance_depth": 1.3,  # 30% more time per level
            "property_variety": 1.2,   # 20% more time per property type
            "class_count": 1.1         # 10% more time per additional class
        }
    
    def map_computational_to_human(self, metrics: TaskMetrics) -> HumanEffortEstimate:
        """Map computational metrics to human effort estimates"""
        
        if "find_value_properties" in metrics.task_name:
            return self._estimate_value_property_analysis(metrics)
        elif "find_superclasses" in metrics.task_name:
            return self._estimate_hierarchy_analysis(metrics)
        else:
            return self._estimate_generic_task(metrics)
    
    def _estimate_value_property_analysis(self, metrics: TaskMetrics) -> HumanEffortEstimate:
        """Estimate human effort for finding value properties"""
        
        # Base cognitive tasks involved
        cognitive_tasks = [
            CognitiveTask.READING_COMPREHENSION,  # Understanding class definitions
            CognitiveTask.PATTERN_MATCHING,       # Matching properties to classes
            CognitiveTask.LOGICAL_REASONING,      # Inheritance reasoning
            CognitiveTask.DOMAIN_KNOWLEDGE_RECALL # IoT/ontology knowledge
        ]
        
        # Calculate base time
        base_time = (
            metrics.classes_analyzed * self.cognitive_task_times[CognitiveTask.READING_COMPREHENSION] +
            metrics.properties_found * self.cognitive_task_times[CognitiveTask.PATTERN_MATCHING] +
            metrics.inheritance_levels * self.cognitive_task_times[CognitiveTask.LOGICAL_REASONING] +
            metrics.properties_found * self.cognitive_task_times[CognitiveTask.DOMAIN_KNOWLEDGE_RECALL]
        )
        
        # Apply complexity multipliers
        complexity_factor = (
            (self.complexity_multipliers["inheritance_depth"] ** metrics.inheritance_levels) *
            (self.complexity_multipliers["property_variety"] ** len(set())) *  # Would need property type diversity
            (self.complexity_multipliers["class_count"] ** (metrics.classes_analyzed / 10))
        )
        
        estimated_time = base_time * complexity_factor
        
        # Cognitive load increases with complexity
        cognitive_load = min(10, 3 + metrics.complexity_score / 5)
        
        # Error probability increases with complexity and cognitive load
        error_probability = min(0.8, 0.1 + (cognitive_load - 3) * 0.1)
        
        # Expertise requirement
        expertise = "expert" if metrics.inheritance_levels > 3 else "intermediate"
        
        return HumanEffortEstimate(
            task_name=metrics.task_name,
            estimated_time_minutes=estimated_time,
            cognitive_load=cognitive_load,
            error_probability=error_probability,
            required_expertise=expertise,
            cognitive_tasks=cognitive_tasks
        )
    
    def _estimate_hierarchy_analysis(self, metrics: TaskMetrics) -> HumanEffortEstimate:
        """Estimate human effort for analyzing class hierarchies"""
        # Similar structure but different cognitive task weights
        pass
    
    def _estimate_generic_task(self, metrics: TaskMetrics) -> HumanEffortEstimate:
        """Generic estimation for other tasks"""
        pass


# Human Cognition Modeling Framework
from dataclasses import dataclass, field
from typing import Optional, Union
import json

@dataclass
class HumanCognitionProfile:
    """Models how humans approach tasks differently from computers"""
    expertise_level: str  # novice, intermediate, expert
    working_memory_capacity: int = 7  # Miller's rule: 7±2 items
    attention_span_minutes: float = 20.0  # Focused attention before fatigue
    pattern_recognition_speed: float = 1.0  # Multiplier for pattern matching
    domain_knowledge_depth: float = 0.5  # 0-1 scale of domain expertise
    mistake_recovery_time: float = 3.0  # Minutes to recover from errors
    confidence_threshold: float = 0.8  # How certain before proceeding
    
    # Human-specific cognitive biases and limitations
    sequential_processing: bool = True  # Humans process sequentially, not parallel
    context_switching_penalty: float = 2.0  # Time penalty for switching tasks
    fatigue_accumulation_rate: float = 0.1  # How quickly cognitive load builds up
    
    # Strategic approach differences
    uses_satisficing: bool = True  # Humans often stop at "good enough"
    relies_on_heuristics: bool = True  # Use mental shortcuts
    performs_iterative_refinement: bool = True  # Gradually improve solutions

@dataclass 
class HumanTaskStrategy:
    """Models how humans strategically approach different tasks"""
    approach_type: str  # "top-down", "bottom-up", "mixed"
    initial_exploration_time: float  # Time spent understanding the problem
    information_gathering_strategy: str  # "comprehensive", "selective", "just-in-time"
    verification_frequency: str  # "continuous", "periodic", "final"
    backtracking_probability: float  # Likelihood of revisiting decisions
    
    # Task decomposition patterns
    chunking_strategy: str  # "hierarchical", "sequential", "thematic"
    max_simultaneous_concepts: int = 5  # Cognitive limit on parallel thinking
    
    # Decision making patterns
    uses_mental_models: bool = True
    relies_on_analogies: bool = True
    seeks_external_validation: bool = True

class HumanCognitionSimulator:
    """Simulates human cognitive processes to estimate realistic effort"""
    
    def __init__(self, profile: HumanCognitionProfile):
        self.profile = profile
        self.accumulated_fatigue = 0.0
        self.context_switches = 0
        self.current_working_memory_load = 0
        
    def simulate_task_execution(self, metrics: TaskMetrics, strategy: HumanTaskStrategy) -> Dict[str, Any]:
        """Simulate how a human would actually execute the task"""
        
        simulation_results = {
            "phases": [],
            "total_time": 0.0,
            "errors_made": 0,
            "context_switches": 0,
            "cognitive_overload_events": 0,
            "backtracking_events": 0,
            "external_lookups": 0
        }
        
        # Phase 1: Problem Understanding & Initial Exploration
        exploration_phase = self._simulate_exploration_phase(metrics, strategy)
        simulation_results["phases"].append(exploration_phase)
        simulation_results["total_time"] += exploration_phase["duration"]
        
        # Phase 2: Information Gathering 
        if strategy.information_gathering_strategy == "comprehensive":
            info_phase = self._simulate_comprehensive_analysis(metrics, strategy)
        else:
            info_phase = self._simulate_selective_analysis(metrics, strategy)
        
        simulation_results["phases"].append(info_phase)
        simulation_results["total_time"] += info_phase["duration"]
        simulation_results["external_lookups"] += info_phase.get("lookups", 0)
        
        # Phase 3: Task Execution with Human Constraints
        execution_phase = self._simulate_constrained_execution(metrics, strategy)
        simulation_results["phases"].append(execution_phase)
        simulation_results["total_time"] += execution_phase["duration"]
        simulation_results["errors_made"] += execution_phase.get("errors", 0)
        simulation_results["backtracking_events"] += execution_phase.get("backtracking", 0)
        
        # Phase 4: Verification & Refinement
        verification_phase = self._simulate_verification_phase(metrics, strategy)
        simulation_results["phases"].append(verification_phase)
        simulation_results["total_time"] += verification_phase["duration"]
        
        return simulation_results
    
    def _simulate_exploration_phase(self, metrics: TaskMetrics, strategy: HumanTaskStrategy) -> Dict[str, Any]:
        """Simulate initial problem understanding phase"""
        
        # Humans need time to understand the scope and context
        base_exploration = strategy.initial_exploration_time
        
        # Complexity increases exploration time non-linearly
        complexity_factor = 1 + (metrics.complexity_score / 10) ** 1.5
        
        # Domain expertise reduces exploration time
        expertise_factor = {
            "novice": 2.0,
            "intermediate": 1.3, 
            "expert": 0.8
        }.get(self.profile.expertise_level, 1.0)
        
        exploration_time = base_exploration * complexity_factor * expertise_factor
        
        # Working memory constraints - humans can only keep limited concepts active
        concepts_to_track = min(metrics.classes_analyzed, self.profile.working_memory_capacity)
        if metrics.classes_analyzed > self.profile.working_memory_capacity:
            # Penalty for exceeding working memory
            exploration_time *= 1.5
            
        return {
            "phase": "exploration", 
            "duration": exploration_time,
            "concepts_identified": concepts_to_track,
            "working_memory_utilized": concepts_to_track / self.profile.working_memory_capacity
        }
    
    def _simulate_comprehensive_analysis(self, metrics: TaskMetrics, strategy: HumanTaskStrategy) -> Dict[str, Any]:
        """Simulate thorough analysis approach"""
        
        # Humans read and process information sequentially
        base_analysis_time = 0.0
        lookups = 0
        
        # Reading comprehension time per class/concept
        reading_time_per_class = 1.5  # minutes per class definition
        base_analysis_time += metrics.classes_analyzed * reading_time_per_class
        
        # Property analysis - humans need to understand each property
        property_analysis_time = 0.8  # minutes per property
        base_analysis_time += metrics.properties_found * property_analysis_time
        
        # Inheritance analysis - exponentially harder for humans
        inheritance_time = metrics.inheritance_levels * 2.5 * (1.4 ** metrics.inheritance_levels)
        base_analysis_time += inheritance_time
        
        # External lookups for unfamiliar concepts
        unfamiliar_concept_rate = 1.0 - self.profile.domain_knowledge_depth
        expected_lookups = int(metrics.classes_analyzed * unfamiliar_concept_rate)
        lookup_time = expected_lookups * 3.0  # 3 minutes per lookup
        base_analysis_time += lookup_time
        lookups = expected_lookups
        
        # Fatigue accumulation
        self.accumulated_fatigue += base_analysis_time * self.profile.fatigue_accumulation_rate
        fatigue_penalty = 1 + self.accumulated_fatigue * 0.2
        
        total_time = base_analysis_time * fatigue_penalty
        
        return {
            "phase": "comprehensive_analysis",
            "duration": total_time,
            "lookups": lookups,
            "fatigue_level": self.accumulated_fatigue
        }
    
    def _simulate_selective_analysis(self, metrics: TaskMetrics, strategy: HumanTaskStrategy) -> Dict[str, Any]:
        """Simulate selective/heuristic-based analysis"""
        
        # Humans use shortcuts and focus on promising areas
        focus_factor = 0.6  # Only analyze 60% of available information initially
        
        focused_classes = int(metrics.classes_analyzed * focus_factor)
        focused_properties = int(metrics.properties_found * focus_factor)
        
        # Faster per-item analysis due to heuristics
        quick_analysis_time = (
            focused_classes * 0.8 +  # Faster class analysis
            focused_properties * 0.5 +  # Pattern-based property selection
            metrics.inheritance_levels * 1.2  # Still need to understand inheritance
        )
        
        # Risk of missing important information
        miss_probability = (1 - focus_factor) * (1 - self.profile.domain_knowledge_depth)
        
        return {
            "phase": "selective_analysis", 
            "duration": quick_analysis_time,
            "coverage": focus_factor,
            "miss_probability": miss_probability,
            "lookups": int(focused_classes * 0.3)  # Fewer lookups
        }
    
    def _simulate_constrained_execution(self, metrics: TaskMetrics, strategy: HumanTaskStrategy) -> Dict[str, Any]:
        """Simulate task execution with human cognitive constraints"""
        
        execution_time = 0.0
        errors = 0
        backtracking_events = 0
        
        # Sequential processing constraint
        if self.profile.sequential_processing:
            # Humans can't parallelize like computers
            sequential_penalty = 1.8
            execution_time += metrics.complexity_score * sequential_penalty
        
        # Working memory overflow handling
        simultaneous_concepts = min(strategy.max_simultaneous_concepts, 
                                  self.profile.working_memory_capacity)
        
        if metrics.classes_analyzed > simultaneous_concepts:
            # Need to chunk the work and switch contexts
            chunks = metrics.classes_analyzed // simultaneous_concepts
            self.context_switches += chunks
            context_switch_penalty = chunks * self.profile.context_switching_penalty
            execution_time += context_switch_penalty
        
        # Error probability based on cognitive load
        cognitive_load = self._calculate_cognitive_load(metrics)
        error_probability = self._calculate_error_probability(cognitive_load)
        expected_errors = max(0, int(metrics.complexity_score * error_probability))
        errors = expected_errors
        
        # Recovery time for errors
        recovery_time = errors * self.profile.mistake_recovery_time
        execution_time += recovery_time
        
        # Backtracking due to satisficing behavior
        if self.profile.uses_satisficing:
            # Humans might need to revisit decisions
            backtracking_probability = strategy.backtracking_probability
            if cognitive_load > 0.7:  # High load increases backtracking
                backtracking_probability *= 1.5
                
            expected_backtracks = int(metrics.complexity_score * backtracking_probability)
            backtracking_events = expected_backtracks
            backtrack_time = expected_backtracks * 4.0  # 4 minutes per backtrack
            execution_time += backtrack_time
        
        return {
            "phase": "execution",
            "duration": execution_time,
            "errors": errors, 
            "backtracking": backtracking_events,
            "cognitive_load": cognitive_load
        }
    
    def _simulate_verification_phase(self, metrics: TaskMetrics, strategy: HumanTaskStrategy) -> Dict[str, Any]:
        """Simulate human verification and quality checking"""
        
        verification_time = 0.0
        
        if strategy.verification_frequency == "continuous":
            # Already accounted for in execution
            verification_time = metrics.complexity_score * 0.2
        elif strategy.verification_frequency == "periodic":
            # Periodic checks during execution
            verification_time = metrics.complexity_score * 0.4
        else:  # final
            # Comprehensive final review
            review_time = (
                metrics.classes_analyzed * 0.5 +  # Quick review per class
                metrics.properties_found * 0.3 +   # Check each property
                metrics.inheritance_levels * 1.0   # Verify inheritance logic
            )
            verification_time = review_time
        
        # Confidence threshold affects verification thoroughness
        if self.profile.confidence_threshold > 0.8:
            verification_time *= 1.3  # More thorough checking
        
        return {
            "phase": "verification",
            "duration": verification_time,
            "thoroughness": self.profile.confidence_threshold
        }
    
    def _calculate_cognitive_load(self, metrics: TaskMetrics) -> float:
        """Calculate current cognitive load (0-1 scale)"""
        
        # Base load from task complexity
        base_load = min(1.0, metrics.complexity_score / 20)
        
        # Working memory utilization
        memory_load = self.current_working_memory_load / self.profile.working_memory_capacity
        
        # Accumulated fatigue
        fatigue_load = min(0.4, self.accumulated_fatigue * 0.1)
        
        # Context switching overhead
        switch_load = min(0.3, self.context_switches * 0.05)
        
        total_load = min(1.0, base_load + memory_load + fatigue_load + switch_load)
        return total_load
    
    def _calculate_error_probability(self, cognitive_load: float) -> float:
        """Calculate probability of making errors based on cognitive state"""
        
        # Base error rate by expertise
        base_error_rate = {
            "novice": 0.15,
            "intermediate": 0.08,
            "expert": 0.03
        }.get(self.profile.expertise_level, 0.10)
        
        # Cognitive load increases error probability exponentially
        load_multiplier = 1 + (cognitive_load ** 2) * 3
        
        # Fatigue increases errors
        fatigue_multiplier = 1 + self.accumulated_fatigue * 0.2
        
        total_error_prob = min(0.8, base_error_rate * load_multiplier * fatigue_multiplier)
        return total_error_prob


class AdvancedEffortMapper(EffortMapper):
    """Enhanced effort mapper that uses human cognition simulation"""
    
    def __init__(self):
        super().__init__()
        self.cognition_profiles = {
            "novice": HumanCognitionProfile(
                expertise_level="novice",
                domain_knowledge_depth=0.2,
                attention_span_minutes=15.0,
                confidence_threshold=0.6
            ),
            "intermediate": HumanCognitionProfile(
                expertise_level="intermediate", 
                domain_knowledge_depth=0.6,
                attention_span_minutes=25.0,
                confidence_threshold=0.75
            ),
            "expert": HumanCognitionProfile(
                expertise_level="expert",
                domain_knowledge_depth=0.9,
                attention_span_minutes=35.0, 
                confidence_threshold=0.9,
                pattern_recognition_speed=1.5
            )
        }
        
        self.task_strategies = {
            "systematic_comprehensive": HumanTaskStrategy(
                approach_type="top-down",
                initial_exploration_time=8.0,
                information_gathering_strategy="comprehensive", 
                verification_frequency="continuous",
                backtracking_probability=0.1
            ),
            "pragmatic_selective": HumanTaskStrategy(
                approach_type="mixed",
                initial_exploration_time=4.0,
                information_gathering_strategy="selective",
                verification_frequency="periodic", 
                backtracking_probability=0.3
            ),
            "expert_intuitive": HumanTaskStrategy(
                approach_type="bottom-up",
                initial_exploration_time=2.0,
                information_gathering_strategy="just-in-time",
                verification_frequency="final",
                backtracking_probability=0.15
            )
        }
    
    def estimate_realistic_human_effort(self, metrics: TaskMetrics, 
                                       profile_type: str = "intermediate",
                                       strategy_type: str = "pragmatic_selective") -> Dict[str, Any]:
        """Estimate human effort using cognitive simulation"""
        
        profile = self.cognition_profiles[profile_type]
        strategy = self.task_strategies[strategy_type]
        
        simulator = HumanCognitionSimulator(profile)
        simulation_results = simulator.simulate_task_execution(metrics, strategy)
        
        # Calculate final metrics
        total_time = simulation_results["total_time"]
        final_cognitive_load = simulator._calculate_cognitive_load(metrics)
        error_probability = simulator._calculate_error_probability(final_cognitive_load)
        
        # Confidence in result quality
        confidence = self._calculate_result_confidence(simulation_results, profile, strategy)
        
        return {
            "estimated_time_minutes": total_time,
            "cognitive_load": final_cognitive_load * 10,  # Scale to 1-10
            "error_probability": error_probability,
            "result_confidence": confidence,
            "expertise_required": profile_type,
            "simulation_details": simulation_results,
            "human_vs_computer_factors": {
                "sequential_processing_penalty": 1.8,
                "working_memory_constraint": profile.working_memory_capacity,
                "context_switching_overhead": simulation_results["context_switches"],
                "fatigue_impact": simulator.accumulated_fatigue,
                "external_dependencies": simulation_results["external_lookups"]
            }
        }
    
    def _calculate_result_confidence(self, simulation_results: Dict, 
                                   profile: HumanCognitionProfile,
                                   strategy: HumanTaskStrategy) -> float:
        """Calculate confidence in the quality of human results"""
        
        base_confidence = profile.confidence_threshold
        
        # Reduce confidence based on shortcuts taken
        if strategy.information_gathering_strategy == "selective":
            for phase in simulation_results["phases"]:
                if phase.get("phase") == "selective_analysis":
                    coverage = phase.get("coverage", 1.0)
                    base_confidence *= coverage
        
        # Reduce confidence based on errors and backtracking
        error_penalty = simulation_results["errors_made"] * 0.1
        backtrack_penalty = simulation_results["backtracking_events"] * 0.05
        
        final_confidence = max(0.1, base_confidence - error_penalty - backtrack_penalty)
        return final_confidence
    
    def compare_human_vs_computational(self, metrics: TaskMetrics) -> Dict[str, Any]:
        """Compare different human approaches vs computational approach"""
        
        results = {
            "computational_baseline": {
                "time_seconds": metrics.execution_time,
                "memory_mb": metrics.memory_peak,
                "accuracy": 1.0,  # Assume perfect computational accuracy
                "completeness": 1.0
            },
            "human_estimates": {}
        }
        
        # Test different human profiles and strategies
        for profile_name in self.cognition_profiles.keys():
            for strategy_name in self.task_strategies.keys():
                human_result = self.estimate_realistic_human_effort(
                    metrics, profile_name, strategy_name
                )
                
                key = f"{profile_name}_{strategy_name}"
                results["human_estimates"][key] = human_result
                
                # Calculate efficiency ratios
                time_ratio = (human_result["estimated_time_minutes"] * 60) / max(0.001, metrics.execution_time)
                results["human_estimates"][key]["time_vs_computer"] = time_ratio
        
        return results