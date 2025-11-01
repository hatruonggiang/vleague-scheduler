from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

@dataclass
class GAConfig:
    """
    Cấu hình các tham số cho Genetic Algorithm
    """
    
    # Kích thước quần thể
    population_size: int = 200
    
    # Số thế hệ
    n_generations: int = 1000
    
    # Xác suất crossover
    crossover_prob: float = 0.8
    
    # Xác suất mutation
    mutation_prob: float = 0.2
    
    # Kích thước tournament selection
    tournament_size: int = 3
    
    # Số cá thể ưu tú được giữ lại (elitism)
    n_elites: int = 2
    
    # Chiến lược khởi tạo quần thể
    init_strategies: Dict[str, float] = field(default_factory=lambda: {
        'random': 0.4,
        'round_robin': 0.2,
        'balanced': 0.2,
        'stadium_aware': 0.2
    })
    
    # Trọng số các ràng buộc mềm
    soft_weights: Dict[str, float] = field(default_factory=lambda: {
        'home_away_balance': 0.25,
        'travel_distance': 0.30,
        'competitive_balance': 0.20,
        'rest_days_fairness': 0.15,
        'derby_distribution': 0.10
    })
    
    # Trọng số phạt các ràng buộc cứng
    penalty_weights: Dict[str, float] = field(default_factory=lambda: {
        'all_matchups': 1000,
        'no_consecutive': 500,
        'one_match_per_round': 1000,
        'stadium_conflict': 800,
        'correct_stadium': 500,
        'total_matches': 1000,
        'matches_per_round': 1000
    })
    
    # Có sử dụng repair sau mutation không
    use_repair: bool = True
    
    # Số lần thử repair tối đa
    max_repair_iterations: int = 50
    
    # Có lưu log không
    enable_logging: bool = True
    
    # Tần suất in thống kê (mỗi n thế hệ)
    log_frequency: int = 10
    
    # Có lưu lịch sử fitness không
    save_history: bool = True
    
    # Điều kiện dừng sớm (early stopping)
    early_stopping: bool = True
    early_stopping_patience: int = 100  # Dừng nếu không cải thiện sau n thế hệ
    early_stopping_min_improvement: float = 0.01  # Cải thiện tối thiểu
    
    # Có áp dụng local search không
    use_local_search: bool = False
    local_search_frequency: int = 50  # Áp dụng mỗi n thế hệ
    
    # Random seed (None = ngẫu nhiên)
    random_seed: Optional[int] = None
    
    def __str__(self) -> str:
        """In cấu hình"""
        return f"""
GA Configuration:
================
Population size: {self.population_size}
Generations: {self.n_generations}
Crossover probability: {self.crossover_prob}
Mutation probability: {self.mutation_prob}
Tournament size: {self.tournament_size}
Elitism: {self.n_elites}
Use repair: {self.use_repair}
Early stopping: {self.early_stopping}
Random seed: {self.random_seed}
"""
    
    def validate(self) -> List[str]:
        """
        Kiểm tra tính hợp lệ của config
        
        Returns: List các lỗi (empty nếu hợp lệ)
        """
        errors = []
        
        if self.population_size < 10:
            errors.append("Population size quá nhỏ (< 10)")
        
        if self.n_generations < 1:
            errors.append("Số thế hệ phải > 0")
        
        if not (0 <= self.crossover_prob <= 1):
            errors.append("Crossover probability phải trong [0, 1]")
        
        if not (0 <= self.mutation_prob <= 1):
            errors.append("Mutation probability phải trong [0, 1]")
        
        if self.tournament_size < 2:
            errors.append("Tournament size phải >= 2")
        
        if self.tournament_size > self.population_size:
            errors.append("Tournament size không được lớn hơn population size")
        
        if self.n_elites < 0:
            errors.append("Số elite phải >= 0")
        
        if self.n_elites >= self.population_size:
            errors.append("Số elite phải < population size")
        
        # Kiểm tra tổng trọng số init strategies
        init_sum = sum(self.init_strategies.values())
        if abs(init_sum - 1.0) > 0.01:
            errors.append(f"Tổng trọng số init_strategies phải = 1.0 (hiện tại: {init_sum})")
        
        # Kiểm tra trọng số soft constraints
        soft_sum = sum(self.soft_weights.values())
        if abs(soft_sum - 1.0) > 0.01:
            errors.append(f"Tổng trọng số soft_weights phải = 1.0 (hiện tại: {soft_sum})")
        
        return errors
    
    def to_dict(self) -> Dict:
        """Convert config sang dictionary"""
        return {
            'population_size': self.population_size,
            'n_generations': self.n_generations,
            'crossover_prob': self.crossover_prob,
            'mutation_prob': self.mutation_prob,
            'tournament_size': self.tournament_size,
            'n_elites': self.n_elites,
            'init_strategies': self.init_strategies,
            'soft_weights': self.soft_weights,
            'penalty_weights': self.penalty_weights,
            'use_repair': self.use_repair,
            'max_repair_iterations': self.max_repair_iterations,
            'enable_logging': self.enable_logging,
            'log_frequency': self.log_frequency,
            'save_history': self.save_history,
            'early_stopping': self.early_stopping,
            'early_stopping_patience': self.early_stopping_patience,
            'early_stopping_min_improvement': self.early_stopping_min_improvement,
            'use_local_search': self.use_local_search,
            'local_search_frequency': self.local_search_frequency,
            'random_seed': self.random_seed
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict) -> 'GAConfig':
        """Tạo config từ dictionary"""
        return cls(**config_dict)
    
    @classmethod
    def quick_test_config(cls) -> 'GAConfig':
        """Tạo config cho test nhanh (ít thế hệ)"""
        return cls(
            population_size=50,
            n_generations=100,
            log_frequency=10,
            early_stopping_patience=20
        )
    
    @classmethod
    def production_config(cls) -> 'GAConfig':
        """Tạo config cho production (nhiều thế hệ, kết quả tốt)"""
        return cls(
            population_size=300,
            n_generations=2000,
            crossover_prob=0.85,
            mutation_prob=0.15,
            tournament_size=5,
            n_elites=5,
            log_frequency=50,
            early_stopping_patience=200,
            use_local_search=True,
            local_search_frequency=100
        )