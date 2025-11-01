import random
import time
from typing import List, Dict, Tuple, Optional
from deap import base, creator, tools
from ..models.team import Team
from ..models.schedule import Schedule
from ..ga.initialization import PopulationInitializer
from ..ga.fitness import FitnessEvaluator
from ..ga.operators import GeneticOperators
from ..ga.repair import ScheduleRepairer
from .config import GAConfig

class GAOptimizer:
    """
    Genetic Algorithm Optimizer chính cho bài toán xếp lịch
    """
    
    def __init__(self, 
                 teams: List[Team],
                 distances: Dict[Tuple[str, str], float],
                 shared_stadiums: Dict[int, List[int]],
                 derby_pairs: List[Tuple[int, int]] = None,
                 config: GAConfig = None):
        """
        Args:
            teams: Danh sách đội bóng
            distances: Ma trận khoảng cách
            shared_stadiums: Dict các sân dùng chung
            derby_pairs: List các cặp derby
            config: Cấu hình GA
        """
        self.teams = teams
        self.distances = distances
        self.shared_stadiums = shared_stadiums
        self.derby_pairs = derby_pairs or []
        self.config = config or GAConfig()
        
        # Validate config
        errors = self.config.validate()
        if errors:
            raise ValueError(f"Config không hợp lệ:\n" + "\n".join(errors))
        
        # Set random seed
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
        
        # Khởi tạo các components
        self.initializer = PopulationInitializer(teams, shared_stadiums)
        self.fitness_evaluator = FitnessEvaluator(
            teams, distances, shared_stadiums, derby_pairs,
            self.config.soft_weights, self.config.penalty_weights
        )
        self.operators = GeneticOperators(teams)
        self.repairer = ScheduleRepairer(teams, shared_stadiums)
        
        # Setup DEAP
        self._setup_deap()
        
        # Lịch sử
        self.history = {
            'best_fitness': [],
            'avg_fitness': [],
            'worst_fitness': [],
            'diversity': [],
            'valid_count': []
        }
        
        self.best_schedule = None
        self.best_fitness = float('-inf')
        
    def _setup_deap(self):
        """
        Setup DEAP framework
        """
        # Xóa nếu đã tồn tại
        if hasattr(creator, "FitnessMax"):
            del creator.FitnessMax
        if hasattr(creator, "Individual"):
            del creator.Individual
        
        # Tạo fitness class (maximize)
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        
        # Tạo individual class
        creator.create("Individual", Schedule, fitness=creator.FitnessMax)
        
        # Tạo toolbox
        self.toolbox = base.Toolbox()
        
        # Đăng ký các operators
        self.toolbox.register("evaluate", self.fitness_evaluator.evaluate)
        self.toolbox.register("mate", self.operators.crossover_round_swap)
        self.toolbox.register("mutate", self.operators.apply_mutation, 
                            mutation_rate=self.config.mutation_prob)
        self.toolbox.register("select", tools.selTournament, 
                            tournsize=self.config.tournament_size)
    
    def optimize(self) -> Schedule:
        """
        Chạy GA optimization
        
        Returns: Schedule tốt nhất tìm được
        """
        print("=" * 70)
        print("BẮT ĐẦU TỐI ƯU HÓA GENETIC ALGORITHM")
        print("=" * 70)
        print(self.config)
        
        start_time = time.time()
        
        # Khởi tạo quần thể
        print("\n1. KHỞI TẠO QUẦN THỂ")
        population = self._initialize_population()
        
        # Đánh giá quần thể ban đầu
        print("\n2. ĐÁNH GIÁ QUẦN THỂ BAN ĐẦU")
        self._evaluate_population(population)
        
        if self.config.enable_logging:
            self.fitness_evaluator.print_population_statistics(population, 0)
        
        # Biến theo dõi early stopping
        generations_without_improvement = 0
        last_best_fitness = float('-inf')
        
        # Vòng lặp chính
        print("\n3. TIẾN HÓA")
        for gen in range(1, self.config.n_generations + 1):
            
            # Selection
            offspring = self.toolbox.select(population, len(population))
            offspring = [self._schedule_to_individual(s) for s in offspring]
            
            # Clone
            offspring = [s.clone() for s in offspring]
            
            # Crossover
            for i in range(0, len(offspring) - 1, 2):
                if random.random() < self.config.crossover_prob:
                    child1, child2 = self.toolbox.mate(offspring[i], offspring[i+1])
                    
                    # Convert về Individual
                    offspring[i] = self._schedule_to_individual(child1)
                    offspring[i+1] = self._schedule_to_individual(child2)

            # Mutation
            for i in range(len(offspring)):
                if random.random() < self.config.mutation_prob:
                    mutated = self.toolbox.mutate(offspring[i])
        
            # Convert về Individual
            offspring[i] = self._schedule_to_individual(mutated)
            
            # Repair nếu cần
            if self.config.use_repair:
                for i in range(len(offspring)):
                    # Repair và convert về Individual
                    repaired = self.repairer.quick_repair(offspring[i])
                    offspring[i] = self._schedule_to_individual(repaired)
            
            # Đánh giá những cá thể mới
            fitnesses = [self.toolbox.evaluate(ind) for ind in offspring]
            for ind, fit in zip(offspring, fitnesses):
                ind.fitness.values = fit
            
            # Elitism: giữ lại các cá thể tốt nhất
            if self.config.n_elites > 0:
                elites = tools.selBest(population, self.config.n_elites)
                offspring = elites + offspring[:-self.config.n_elites]
            
            # Thay thế quần thể
            population[:] = offspring
            
            # Lưu lịch sử
            if self.config.save_history:
                self._update_history(population)
            
            # Cập nhật best schedule
            current_best = self._get_best(population)
            current_best_fitness = current_best.fitness.values[0]
            
            if current_best_fitness > self.best_fitness:
                self.best_fitness = current_best_fitness
                self.best_schedule = current_best.clone()
            
            # Logging
            if self.config.enable_logging and gen % self.config.log_frequency == 0:
                self.fitness_evaluator.print_population_statistics(population, gen)
                elapsed = time.time() - start_time
                print(f"Thời gian đã trôi qua: {elapsed:.2f}s")
                print(f"Best fitness từ trước đến nay: {self.best_fitness:.2f}")
                print("-" * 70)
            
            # Local search
            if self.config.use_local_search and gen % self.config.local_search_frequency == 0:
                print(f"\nÁp dụng local search tại thế hệ {gen}...")
                population = self._apply_local_search(population)
            
            # Early stopping
            if self.config.early_stopping:
                improvement = current_best_fitness - last_best_fitness
                
                if improvement < self.config.early_stopping_min_improvement:
                    generations_without_improvement += 1
                else:
                    generations_without_improvement = 0
                
                if generations_without_improvement >= self.config.early_stopping_patience:
                    print(f"\nEarly stopping tại thế hệ {gen}")
                    print(f"Không có cải thiện sau {self.config.early_stopping_patience} thế hệ")
                    break
                
                last_best_fitness = current_best_fitness
        
        # Kết thúc
        end_time = time.time()
        total_time = end_time - start_time
        
        print("\n" + "=" * 70)
        print("KẾT THÚC TỐI ƯU HÓA")
        print("=" * 70)
        print(f"Tổng thời gian: {total_time:.2f}s")
        print(f"Fitness tốt nhất: {self.best_fitness:.2f}")
        
        # In báo cáo chi tiết
        print("\n" + "=" * 70)
        self.fitness_evaluator.constraint_checker.print_report(self.best_schedule)
        
        return self.best_schedule
    
    def _initialize_population(self) -> List[Schedule]:
        """Khởi tạo quần thể"""
        population = self.initializer.initialize_population(
            self.config.population_size,
            self.config.init_strategies
        )
        
        # Convert sang Individual
        population = [self._schedule_to_individual(s) for s in population]
        
        return population
    
    def _schedule_to_individual(self, schedule: Schedule):
        """Convert Schedule sang DEAP Individual"""
        ind = creator.Individual(matches=schedule.matches[:])
        return ind
    
    def _evaluate_population(self, population: List[Schedule]):
        """Đánh giá toàn bộ quần thể"""
        fitnesses = [self.toolbox.evaluate(ind) for ind in population]
        for ind, fit in zip(population, fitnesses):
            ind.fitness.values = fit
    
    def _get_best(self, population: List[Schedule]) -> Schedule:
        """Lấy cá thể tốt nhất"""
        return tools.selBest(population, 1)[0]
    
    def _update_history(self, population: List[Schedule]):
        """Cập nhật lịch sử"""
        fitnesses = [ind.fitness.values[0] for ind in population]
        
        self.history['best_fitness'].append(max(fitnesses))
        self.history['avg_fitness'].append(sum(fitnesses) / len(fitnesses))
        self.history['worst_fitness'].append(min(fitnesses))
        
        # Đếm số lịch hợp lệ
        valid_count = sum(1 for s in population 
                         if self.fitness_evaluator.is_valid_schedule(s))
        self.history['valid_count'].append(valid_count)
        
        # Tính diversity
        diversity = self.fitness_evaluator.calculate_diversity(population)
        self.history['diversity'].append(diversity)
    
    def _apply_local_search(self, population: List[Schedule]) -> List[Schedule]:
        """
        Áp dụng local search cho một số cá thể tốt nhất
        
        Local search: thử hoán đổi một số trận để cải thiện fitness
        """
        n_improve = min(5, len(population) // 10)
        best_individuals = tools.selBest(population, n_improve)
        
        improved = []
        for ind in best_individuals:
            improved_ind = self._local_search_one(ind)
            improved.append(improved_ind)
        
        # Thay thế các cá thể tệ nhất
        worst_indices = sorted(range(len(population)), 
                              key=lambda i: population[i].fitness.values[0])[:n_improve]
        
        for idx, imp in zip(worst_indices, improved):
            population[idx] = imp
        
        return population
    
    def _local_search_one(self, schedule: Schedule, n_iterations: int = 10) -> Schedule:
        """
        Local search cho một cá thể
        """
        current = schedule.clone()
        current_fitness = self.toolbox.evaluate(current)[0]
        
        for _ in range(n_iterations):
            # Thử một mutation nhỏ
            neighbor = self.operators.mutate_swap_matches(current)
            neighbor_fitness = self.toolbox.evaluate(neighbor)[0]
            
            # Chấp nhận nếu tốt hơn
            if neighbor_fitness > current_fitness:
                current = neighbor
                current_fitness = neighbor_fitness
        
        # Set fitness
        ind = self._schedule_to_individual(current)
        ind.fitness.values = (current_fitness,)
        
        return ind
    
    def get_history(self) -> Dict:
        """Lấy lịch sử"""
        return self.history
    
    def plot_history(self, save_path: str = None):
        """
        Vẽ biểu đồ lịch sử fitness
        
        Args:
            save_path: Đường dẫn lưu file (None = hiển thị)
        """
        try:
            import matplotlib.pyplot as plt
            
            generations = range(len(self.history['best_fitness']))
            
            plt.figure(figsize=(12, 8))
            
            # Subplot 1: Fitness evolution
            plt.subplot(2, 1, 1)
            plt.plot(generations, self.history['best_fitness'], label='Best', linewidth=2)
            plt.plot(generations, self.history['avg_fitness'], label='Average', linewidth=2)
            plt.plot(generations, self.history['worst_fitness'], label='Worst', linewidth=2)
            plt.xlabel('Generation')
            plt.ylabel('Fitness')
            plt.title('Fitness Evolution')
            plt.legend()
            plt.grid(True)
            
            # Subplot 2: Valid schedules count
            plt.subplot(2, 1, 2)
            plt.plot(generations, self.history['valid_count'], linewidth=2, color='green')
            plt.xlabel('Generation')
            plt.ylabel('Number of Valid Schedules')
            plt.title('Valid Schedules Count')
            plt.grid(True)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"Đã lưu biểu đồ tại: {save_path}")
            else:
                plt.show()
            
            plt.close()
            
        except ImportError:
            print("Cần cài matplotlib để vẽ biểu đồ: pip install matplotlib")