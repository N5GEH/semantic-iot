import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score
from scipy.optimize import minimize
import matplotlib.pyplot as plt

class KnowledgeGraphIRT:
    """
    Item Response Theory implementation for Knowledge Graph generation tasks
    """
    
    def __init__(self):
        self.item_params = {}  # {task_id: {'difficulty': beta, 'discrimination': alpha}}
        self.model_abilities = {}  # {model_id: theta}
        self.response_matrix = None
        
    def collect_responses(self, tasks, models, evaluator_func):
        """
        Step 1: Collect binary responses from models on tasks
        
        Args:
            tasks: List of knowledge graph generation tasks
            models: List of CodeLLMs to evaluate
            evaluator_func: Function that returns 1 (correct) or 0 (incorrect)
        
        Returns:
            response_matrix: DataFrame with models as rows, tasks as columns
        """
        responses = []
        
        for model in models:
            model_responses = []
            for task in tasks:
                # Generate knowledge graph with model
                generated_kg = self.generate_kg_with_model(model, task)
                
                # Evaluate correctness (binary)
                score = evaluator_func(generated_kg, task['ground_truth'])
                model_responses.append(score)
            
            responses.append(model_responses)
        
        self.response_matrix = pd.DataFrame(
            responses, 
            index=[m['name'] for m in models],
            columns=[f"task_{i}" for i in range(len(tasks))]
        )
        
        return self.response_matrix
    
    def generate_kg_with_model(self, model, task):
        """
        Generate knowledge graph using specified model
        This would interface with your actual models (GPT-4, Claude, etc.)
        """
        # Placeholder - implement actual model inference
        prompt = self.create_kg_prompt(task)
        response = model.generate(prompt)  # Your model API call
        return self.parse_kg_response(response)
    
    def create_kg_prompt(self, task):
        """Create standardized prompt for knowledge graph generation"""
        return f"""
        Generate a knowledge graph from the following JSON entities:
        
        Entities: {task['entities']}
        Mappings: {task['mappings']}
        
        Output format: RDF triples or your specified format
        """
    
    def evaluate_kg_correctness(self, generated_kg, ground_truth):
        """
        Binary evaluation of knowledge graph correctness
        
        Returns:
            1 if correct/acceptable, 0 if incorrect
        """
        # Implement your evaluation logic
        # Could be based on:
        # - Structural correctness
        # - Semantic accuracy  
        # - Completeness
        # - Ontology compliance
        
        correctness_score = self.calculate_kg_similarity(generated_kg, ground_truth)
        return 1 if correctness_score > 0.8 else 0  # Binary threshold
    
    def fit_irt_model(self, max_iterations=1000):
        """
        Step 2: Fit IRT model using Maximum Likelihood Estimation
        
        Uses 2-Parameter Logistic Model (2PL):
        P(X_ij = 1) = 1 / (1 + exp(-a_i(θ_j - b_i)))
        
        Where:
        - a_i: discrimination parameter for item i
        - b_i: difficulty parameter for item i  
        - θ_j: ability parameter for person j
        """
        if self.response_matrix is None:
            raise ValueError("Must collect responses first")
        
        n_models, n_tasks = self.response_matrix.shape
        
        # Initialize parameters
        initial_params = np.concatenate([
            np.ones(n_tasks),      # discriminations (a)
            np.zeros(n_tasks),     # difficulties (b)
            np.zeros(n_models)     # abilities (theta)
        ])
        
        # Optimize using maximum likelihood
        result = minimize(
            self._negative_log_likelihood,
            initial_params,
            args=(self.response_matrix.values,),
            method='BFGS',
            options={'maxiter': max_iterations}
        )
        
        # Extract fitted parameters
        params = result.x
        discriminations = params[:n_tasks]
        difficulties = params[n_tasks:2*n_tasks]
        abilities = params[2*n_tasks:]
        
        # Store results
        task_names = self.response_matrix.columns
        model_names = self.response_matrix.index
        
        for i, task in enumerate(task_names):
            self.item_params[task] = {
                'discrimination': discriminations[i],
                'difficulty': difficulties[i]
            }
        
        for j, model in enumerate(model_names):
            self.model_abilities[model] = abilities[j]
        
        return result
    
    def _negative_log_likelihood(self, params, response_matrix):
        """Calculate negative log-likelihood for optimization"""
        n_models, n_tasks = response_matrix.shape
        
        discriminations = params[:n_tasks]
        difficulties = params[n_tasks:2*n_tasks]
        abilities = params[2*n_tasks:]
        
        log_likelihood = 0
        
        for i in range(n_models):
            for j in range(n_tasks):
                # 2PL model probability
                linear_pred = discriminations[j] * (abilities[i] - difficulties[j])
                prob = 1 / (1 + np.exp(-linear_pred))
                
                # Avoid log(0)
                prob = np.clip(prob, 1e-10, 1-1e-10)
                
                if response_matrix[i, j] == 1:
                    log_likelihood += np.log(prob)
                else:
                    log_likelihood += np.log(1 - prob)
        
        return -log_likelihood
    
    def predict_difficulty(self, task_features):
        """
        Step 3: Predict difficulty for new tasks using LLM-based features
        
        Args:
            task_features: Dictionary with semantic complexity metrics from LLM
        
        Returns:
            predicted_difficulty: Estimated difficulty parameter
        """
        # This would use your LLM-based complexity assessment
        # to predict IRT difficulty parameter
        
        complexity_score = (
            task_features.get('semantic_distance', 0) * 0.3 +
            task_features.get('domain_knowledge_required', 0) * 0.4 +
            task_features.get('inference_complexity', 0) * 0.3
        )
        
        # Convert to IRT difficulty scale (could use regression fitted on known tasks)
        predicted_difficulty = -2.0 + (complexity_score / 5.0) * 4.0  # Scale to [-2, 2]
        
        return predicted_difficulty
    
    def generate_difficulty_report(self):
        """Generate comprehensive difficulty analysis"""
        report = {
            'task_difficulties': self.item_params,
            'model_abilities': self.model_abilities,
            'hardest_tasks': self._get_hardest_tasks(),
            'most_discriminating_tasks': self._get_most_discriminating_tasks(),
            'model_rankings': self._rank_models()
        }
        
        return report
    
    def _get_hardest_tasks(self, top_k=5):
        """Get tasks with highest difficulty parameters"""
        difficulties = [(task, params['difficulty']) 
                       for task, params in self.item_params.items()]
        return sorted(difficulties, key=lambda x: x[1], reverse=True)[:top_k]
    
    def _get_most_discriminating_tasks(self, top_k=5):
        """Get tasks with highest discrimination parameters"""
        discriminations = [(task, params['discrimination']) 
                          for task, params in self.item_params.items()]
        return sorted(discriminations, key=lambda x: x[1], reverse=True)[:top_k]
    
    def _rank_models(self):
        """Rank models by ability parameter"""
        abilities = [(model, ability) for model, ability in self.model_abilities.items()]
        return sorted(abilities, key=lambda x: x[1], reverse=True)
    
    def plot_item_characteristic_curves(self, task_ids=None):
        """Plot Item Characteristic Curves for visualization"""
        if task_ids is None:
            task_ids = list(self.item_params.keys())[:5]  # Plot first 5 tasks
        
        theta_range = np.linspace(-3, 3, 100)
        
        plt.figure(figsize=(10, 6))
        
        for task_id in task_ids:
            params = self.item_params[task_id]
            a, b = params['discrimination'], params['difficulty']
            
            # Calculate probabilities across ability range
            probs = 1 / (1 + np.exp(-a * (theta_range - b)))
            
            plt.plot(theta_range, probs, label=f'{task_id} (a={a:.2f}, b={b:.2f})')
        
        plt.xlabel('Model Ability (θ)')
        plt.ylabel('Probability of Correct Response')
        plt.title('Item Characteristic Curves')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()

# Example usage workflow
def main_workflow():
    """Complete workflow example"""
    
    # Initialize IRT system
    irt_system = KnowledgeGraphIRT()
    
    # Step 1: Define your tasks and models
    tasks = [
        {
            'id': 'simple_hotel',
            'entities': 'your_json_entities_here',
            'mappings': 'your_mappings_here',
            'ground_truth': 'expected_knowledge_graph'
        },
        # ... more tasks
    ]
    
    models = [
        {'name': 'GPT-4', 'api': 'openai_api'},
        {'name': 'Claude-3', 'api': 'anthropic_api'},
        {'name': 'CodeLlama', 'api': 'huggingface_api'},
        # ... more models
    ]
    
    # Step 2: Collect responses
    response_matrix = irt_system.collect_responses(
        tasks, models, irt_system.evaluate_kg_correctness
    )
    
    # Step 3: Fit IRT model
    fit_result = irt_system.fit_irt_model()
    
    # Step 4: Analyze results
    report = irt_system.generate_difficulty_report()
    print("Difficulty Analysis:", report)
    
    # Step 5: Plot results
    irt_system.plot_item_characteristic_curves()
    
    # Step 6: Use LLM for new task difficulty prediction
    new_task_features = {
        'semantic_distance': 4.2,
        'domain_knowledge_required': 3.8,
        'inference_complexity': 4.1
    }
    
    predicted_difficulty = irt_system.predict_difficulty(new_task_features)
    print(f"Predicted difficulty for new task: {predicted_difficulty}")

if __name__ == "__main__":
    main_workflow()