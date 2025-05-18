import sys
from pathlib import Path
import json
sys.path.append(str(Path(__file__).parent.parent))  # Add LLM_models to path
from semantic_iot.claude import ClaudeAPIProcessor
import time
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from typing import Dict, List, Any, Optional, Union, Tuple

# Instead of passing metrics directly, pass the claude object?

class MetricsEval:
    def __init__(self):
        self.claude = ClaudeAPIProcessor()

    def quantify_thinking(self, metrics_dict: dict) -> str:
        """
        Extract thinking processes from metrics dictionary and evaluate them
        
        Args:
            metrics_dict: Dictionary containing metrics with thinking process for each step
            
        Returns:
            str: The response from the Claude API
        """

        print(f"Metrics Dictionary: {metrics_dict}")

        prompt = f"""
            Based on the thinking process of each different step in the metrics <data>{metrics_dict}</data>, 
            compare the amount of effort a human would need for each step. 

            For each of the following metrics, evaluate a score for each step. Important are not the absolute values but the relative proportions between the steps.
            Give a rating of 1 (minimal human effort) to 100 (maximal human effort).

            - Difficulty
                - Cognitive Load: How difficult is it for a human to understand the step?
                    - Working memory load (measured via information units managed simultaneously)
                    - Processing complexity (quantified through required cognitive operations)
                    - Expertise reliance (assessed via knowledge depth utilization)
                    - Mental model construction (measured through conceptual mapping requirements)
                    - Problem-solving novelty (rated by solution pattern familiarity/innovation)

            - Time
                - Temporal Investment
                    - Duration allocation (tracked by task/subtask time measurements)
                - Attentional Quality
                    - Focus density (measured through deep work vs. shallow work ratios)
                    - Context switching costs (assessed via productivity loss during transitions)
                - Decision Processing
                    - Decision quantity (counted by choice points per time unit)
                    - Decision complexity (rated by option evaluation requirements)
                    - Decision automation potential (measured by percentage of decisions that could be
                      handled by rules/algorithms vs. requiring human judgment)

            - Accuracy
                - Error Rate
                - Refinement iterations
            
            - Human Effort Index
                - Aggregate score combining the above metrics to quantify overall human effort required
                  (calculated as weighted average: 40% Cognitive Load, 30% Time factors, 30% Accuracy factors)
                
            Consider the IoT and semantic web domain context when evaluating these metrics. 
            Tasks involving semantic mapping, ontology alignment, and IoT device integration generally 
            require higher expertise and mental model construction than standard programming tasks.

            
            Return a JSON object where you put all generated effort scores 
            within the evaluation section in the same hierarchical structure:

            {{
                "step_name": {{
                    "evaluation": {{
                        
                    }}
                }}
            }}
            
        """
        
        response = self.claude.query(step_name="📐 Compare Metrics", thinking=True, prompt=prompt)

        print(response)
        print(f"\nMetrics: {self.claude.metrics}")

        if isinstance(response, str):
            try:
                response_dict = json.loads(response)
                new_metrics = response_dict.get("metrics", {})
            except json.JSONDecodeError:
                new_metrics = {}
        else:
            new_metrics = response.get("metrics", {})

        # Merge the response with the existing metrics
        for step_name, step_metrics in metrics_dict.items():
            if step_name not in self.claude.metrics:
                self.claude.metrics[step_name] = {}
            self.claude.metrics[step_name].update(step_metrics)

        

        return response

    def visualize_metrics(self, metrics_dict: Dict[str, Dict[str, Any]], 
                       output_path: Optional[str] = None,
                       show_plot: bool = True,
                       chart_type: str = "radar") -> None:
        """
        Visualize metrics data from Claude's evaluation
        
        Args:
            metrics_dict: Dictionary with metrics data
            output_path: Optional path to save the visualization
            show_plot: Whether to display the plot
            chart_type: Type of chart to create (radar, bar, heatmap)
        """
        # Extract evaluation metrics if they exist
        eval_metrics = {}
        
        for step_name, step_data in metrics_dict.items():
            if "evaluation" in step_data:
                eval_metrics[step_name] = step_data["evaluation"]
        
        if not eval_metrics:
            print("No evaluation metrics found in the provided dictionary")
            return
            
        # Choose visualization method based on chart_type
        if chart_type.lower() == "radar":
            self._create_radar_chart(eval_metrics, output_path, show_plot)
        elif chart_type.lower() == "bar":
            self._create_bar_chart(eval_metrics, output_path, show_plot)
        elif chart_type.lower() == "heatmap":
            self._create_heatmap(eval_metrics, output_path, show_plot)
        else:
            print(f"Unsupported chart type: {chart_type}. Using radar chart instead.")
            self._create_radar_chart(eval_metrics, output_path, show_plot)
    
    def _create_radar_chart(self, eval_metrics: Dict[str, Dict[str, Any]], 
                           output_path: Optional[str] = None,
                           show_plot: bool = True) -> None:
        """Create a radar chart for the metrics"""
        # Determine common metrics across all steps
        common_metrics = self._get_common_metrics(eval_metrics)
        
        if not common_metrics:
            print("No common metrics found across all steps")
            return
            
        # Set up the radar chart
        step_names = list(eval_metrics.keys())
        num_steps = len(step_names)
        
        # Set up angles for radar chart
        angles = np.linspace(0, 2*np.pi, len(common_metrics), endpoint=False).tolist()
        angles += angles[:1]  # Close the loop
        
        # Set up figure
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(polar=True))
        
        # Get a color map for different steps
        colors = cm.rainbow(np.linspace(0, 1, num_steps))
        
        # Plot each step
        for i, step_name in enumerate(step_names):
            # Extract values for this step
            values = [eval_metrics[step_name].get(metric, 0) for metric in common_metrics]
            values += values[:1]  # Close the loop
            
            # Plot the step data
            ax.plot(angles, values, 'o-', linewidth=2, color=colors[i], label=step_name, alpha=0.8)
            ax.fill(angles, values, color=colors[i], alpha=0.1)
        
        # Set up radar chart labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(common_metrics, size=10)
        
        # Add legend and title
        ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
        plt.title("Metrics Comparison Across Steps", size=15, y=1.1)
        
        # Save if output path provided
        if output_path:
            plt.tight_layout()
            plt.savefig(output_path)
            print(f"Saved radar chart to {output_path}")
            
        # Show if requested
        if show_plot:
            plt.tight_layout()
            plt.show()
        else:
            plt.close()
    
    def _create_bar_chart(self, eval_metrics: Dict[str, Dict[str, Any]], 
                         output_path: Optional[str] = None,
                         show_plot: bool = True) -> None:
        """Create a bar chart for the metrics"""
        # Determine common metrics across all steps
        common_metrics = self._get_common_metrics(eval_metrics)
        
        if not common_metrics:
            print("No common metrics found across all steps")
            return
            
        # Set up the bar chart
        step_names = list(eval_metrics.keys())
        num_steps = len(step_names)
        num_metrics = len(common_metrics)
        
        # Create position indices for bars
        x = np.arange(num_metrics)
        width = 0.8 / num_steps  # Width of bars
        
        # Set up figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Get a color map for different steps
        colors = cm.rainbow(np.linspace(0, 1, num_steps))
        
        # Plot each step's bars
        for i, step_name in enumerate(step_names):
            # Extract values for this step
            values = [eval_metrics[step_name].get(metric, 0) for metric in common_metrics]
            
            # Plot the bars
            ax.bar(x + i*width - (num_steps-1)*width/2, values, width, label=step_name, color=colors[i], alpha=0.8)
        
        # Set up labels and title
        ax.set_xlabel("Metrics")
        ax.set_ylabel("Values")
        ax.set_title("Metrics Comparison Across Steps")
        ax.set_xticks(x)
        ax.set_xticklabels(common_metrics, rotation=45, ha="right")
        ax.legend()
        
        # Save if output path provided
        if output_path:
            plt.tight_layout()
            plt.savefig(output_path)
            print(f"Saved bar chart to {output_path}")
            
        # Show if requested
        if show_plot:
            plt.tight_layout()
            plt.show()
        else:
            plt.close()
    
    def _create_heatmap(self, eval_metrics: Dict[str, Dict[str, Any]], 
                        output_path: Optional[str] = None,
                        show_plot: bool = True) -> None:
        """Create a heatmap for the metrics"""
        # Determine common metrics across all steps
        common_metrics = self._get_common_metrics(eval_metrics)
        
        if not common_metrics:
            print("No common metrics found across all steps")
            return
            
        # Set up the heatmap data
        step_names = list(eval_metrics.keys())
        
        # Create data matrix
        data_matrix = np.zeros((len(step_names), len(common_metrics)))
        
        for i, step_name in enumerate(step_names):
            for j, metric in enumerate(common_metrics):
                data_matrix[i, j] = eval_metrics[step_name].get(metric, 0)
        
        # Set up figure
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create heatmap
        im = ax.imshow(data_matrix, cmap='viridis')
        
        # Add colorbar
        cbar = ax.figure.colorbar(im, ax=ax)
        cbar.ax.set_ylabel("Values", rotation=-90, va="bottom")
        
        # Set up labels
        ax.set_xticks(np.arange(len(common_metrics)))
        ax.set_yticks(np.arange(len(step_names)))
        ax.set_xticklabels(common_metrics, rotation=45, ha="right")
        ax.set_yticklabels(step_names)
        
        # Add value annotations
        for i in range(len(step_names)):
            for j in range(len(common_metrics)):
                ax.text(j, i, f"{data_matrix[i, j]:.1f}", 
                        ha="center", va="center", 
                        color="white" if data_matrix[i, j] > 50 else "black")
        
        # Title
        ax.set_title("Metrics Heatmap Across Steps")
        
        # Save if output path provided
        if output_path:
            plt.tight_layout()
            plt.savefig(output_path)
            print(f"Saved heatmap to {output_path}")
            
        # Show if requested
        if show_plot:
            plt.tight_layout()
            plt.show()
        else:
            plt.close()
    
    def _get_common_metrics(self, eval_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """Find common metrics across all steps"""
        if not eval_metrics:
            return []
            
        # Get all metrics from the first step
        first_step = next(iter(eval_metrics.values()))
        if first_step is None:
            return []
            
        common_metrics = set(first_step.keys())
        
        # Find intersection with all other steps
        for step_data in eval_metrics.values():
            if step_data is not None:
                common_metrics = common_metrics.intersection(step_data.keys())
            
        return list(common_metrics)
        
    def visualize_memory_usage(self, metrics_dict: Dict[str, Dict[str, Any]], 
                              output_path: Optional[str] = None,
                              show_plot: bool = True) -> None:
        """
        Visualize memory usage over time
        
        Args:
            metrics_dict: Dictionary with metrics data
            output_path: Optional path to save the visualization
            show_plot: Whether to display the plot
        """
        # Check for memory metrics
        memory_data = {}
        
        for step_name, step_data in metrics_dict.items():
            if "memory" in step_data:
                memory_data[step_name] = step_data["memory"]
        
        if not memory_data:
            print("No memory usage data found in the provided dictionary")
            return
            
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Get a color map for different steps
        colors = cm.rainbow(np.linspace(0, 1, len(memory_data)))
        
        # Plot each step's memory usage
        for i, (step_name, memory_values) in enumerate(memory_data.items()):
            ax.plot(memory_values, label=step_name, color=colors[i], alpha=0.8)
        
        # Set up labels and title
        ax.set_xlabel("Measurement Index")
        ax.set_ylabel("Memory Usage (MB)")
        ax.set_title("Memory Usage Over Time")
        ax.legend()
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Save if output path provided
        if output_path:
            plt.tight_layout()
            plt.savefig(output_path)
            print(f"Saved memory usage plot to {output_path}")
            
        # Show if requested
        if show_plot:
            plt.tight_layout()
            plt.show()
        else:
            plt.close()
            
    def visualize_time_comparison(self, metrics_dict: Dict[str, Dict[str, Any]], 
                                output_path: Optional[str] = None,
                                show_plot: bool = True) -> None:
        """
        Visualize time usage comparison
        
        Args:
            metrics_dict: Dictionary with metrics data
            output_path: Optional path to save the visualization
            show_plot: Whether to display the plot
        """
        # Check for time metrics
        time_data = {}
        
        for step_name, step_data in metrics_dict.items():
            if "time" in step_data:
                time_data[step_name] = step_data["time"]
        
        if not time_data:
            print("No time usage data found in the provided dictionary")
            return
            
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Get step names and time values
        step_names = list(time_data.keys())
        time_values = list(time_data.values())
        
        # Create bar chart
        bars = ax.bar(step_names, time_values, color=cm.viridis(np.linspace(0, 1, len(step_names))))
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f"{height:.2f}s", ha='center', va='bottom')
        
        # Set up labels and title
        ax.set_xlabel("Steps")
        ax.set_ylabel("Time (seconds)")
        ax.set_title("Time Usage Comparison")
        
        # Add grid
        ax.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        # Save if output path provided
        if output_path:
            plt.tight_layout()
            plt.savefig(output_path)
            print(f"Saved time comparison plot to {output_path}")
            
        # Show if requested
        if show_plot:
            plt.tight_layout()
            plt.show()
        else:
            plt.close()
        

if __name__ == "__main__":

    # Generate Example Data
    claude = ClaudeAPIProcessor()

    print("Generating example data...")
    response = claude.query("What is 1+2", thinking=True, step_name="Step 1")
    print(f"Step 1 response: {response}")

    response = claude.query("What is sum of natural numbers less than three?", thinking=True, step_name="Step 2")
    print(f"Step 2 response: {response}")

    response = claude.query("What are the first five prime numbers?", thinking=True, step_name="Step 3")
    print(f"Step 3 response: {response}")

    print("Example data generated.")
    print(claude.metrics)
    input("Press Enter to continue...")

    # Add example metric evaluations for demonstration
    for step_name in claude.metrics:

        claude.metrics[step_name]["evaluation"] = {
            "Cognitive_Load": 30 + (hash(step_name) % 40),  # Random-ish value between 30-70
            "Working_Memory_Load": 25 + (hash(step_name[::-1]) % 50),
            "Processing_Complexity": 35 + (hash(step_name + "complexity") % 40),
            "Expertise_Reliance": 40 + (hash(step_name + "expertise") % 30),
            "Time_Investment": 45 + (hash(step_name + "time") % 35),
            "Human_Effort_Index": 50 + (hash(step_name + "effort") % 30)
        }
    print("\nMetrics structure:")
    print(json.dumps(claude.metrics, indent=2))
    input("Press Enter to continue...")
    
    # Print the evaluation structure specifically to debug
    print("\nEvaluation structure:")
    eval_metrics = {}
    for step_name, step_data in claude.metrics.items():
        if "evaluation" in step_data:
            eval_metrics[step_name] = step_data["evaluation"]
    print(json.dumps(eval_metrics, indent=2))

    # Initialize MetricsEval
    met = MetricsEval()
    response = met.quantify_thinking(claude.metrics)
    
    # Create visualizations
    print("\nGenerating visualizations...")
    
    # 1. Radar chart visualization
    met.visualize_metrics(claude.metrics, 
                        output_path="figures/metrics_radar_chart.png", 
                        chart_type="radar")
    
    # 2. Bar chart visualization
    met.visualize_metrics(claude.metrics, 
                        output_path="figures/metrics_bar_chart.png", 
                        chart_type="bar")
    
    # 3. Heatmap visualization
    met.visualize_metrics(claude.metrics, 
                        output_path="figures/metrics_heatmap.png", 
                        chart_type="heatmap")
    
    # 4. If memory usage is available
    if any("memory" in metrics for metrics in claude.metrics.values()):
        met.visualize_memory_usage(claude.metrics, 
                                output_path="figures/memory_usage.png")
    
    # 5. If time usage is available
    if any("time" in metrics for metrics in claude.metrics.values()):
        met.visualize_time_comparison(claude.metrics, 
                                    output_path="figures/time_usage.png")
    
    print("\nVisualization complete. Check the output files in the current directory.")

