from typing import List, Dict, Tuple
from ..models.schedule import Schedule
from ..models.team import Team
from ..constraints.checker import ConstraintChecker

class FitnessEvaluator:
    """
    Đánh giá fitness cho GA
    """
    
    def __init__(self, 
                 teams: List[Team],
                 distances: Dict[Tuple[str, str], float],
                 shared_stadiums: Dict[int, List[int]],
                 derby_pairs: List[Tuple[int, int]] = None,
                 soft_weights: Dict[str, float] = None,
                 penalty_weights: Dict[str, float] = None):
        """
        Args:
            teams: Danh sách đội bóng
            distances: Ma trận khoảng cách
            shared_stadiums: Dict các sân dùng chung
            derby_pairs: List các cặp derby
            soft_weights: Trọng số soft constraints
            penalty_weights: Trọng số phạt hard constraints
        """
        self.teams = teams
        self.constraint_checker = ConstraintChecker(
            teams, distances, shared_stadiums, derby_pairs, soft_weights
        )
        
        # Trọng số phạt cho các vi phạm hard constraints
        if penalty_weights is None:
            self.penalty_weights = {
                'all_matchups': 1000,
                'no_consecutive': 500,
                'one_match_per_round': 1000,
                'stadium_conflict': 800,
                'correct_stadium': 500,
                'total_matches': 1000,
                'matches_per_round': 1000
            }
        else:
            self.penalty_weights = penalty_weights
    
    def evaluate(self, schedule: Schedule) -> Tuple[float]:
        """
        Đánh giá fitness của một schedule
        
        Fitness = soft_score - penalties
        
        Returns: Tuple chứa một giá trị fitness (DEAP yêu cầu tuple)
        """
        result = self.constraint_checker.check_schedule(schedule)
        
        # Lấy soft score
        soft_score = result['soft_constraints']['weighted_score']
        
        # Tính penalties từ hard constraints
        penalties = 0.0
        
        if not result['hard_constraints']['valid']:
            for constraint_name, (is_valid, violations) in result['hard_constraints']['details'].items():
                if not is_valid:
                    penalty_weight = self.penalty_weights.get(constraint_name, 500)
                    penalties += violations * penalty_weight
        
        # Fitness = soft_score - penalties
        # Fitness có thể âm nếu vi phạm nhiều
        fitness = soft_score - penalties
        
        # Lưu fitness vào schedule
        schedule.fitness_score = fitness
        
        return (fitness,)
    
    def evaluate_population(self, population: List[Schedule]) -> List[Tuple[float]]:
        """
        Đánh giá fitness cho toàn bộ quần thể
        
        Returns: List các fitness scores
        """
        fitness_scores = []
        
        for i, schedule in enumerate(population):
            fitness = self.evaluate(schedule)
            fitness_scores.append(fitness)
            
            if (i + 1) % 50 == 0:
                print(f"  Đã đánh giá: {i + 1}/{len(population)} cá thể")
        
        return fitness_scores
    
    def get_detailed_evaluation(self, schedule: Schedule) -> Dict:
        """
        Lấy đánh giá chi tiết của schedule
        
        Returns: Dict chứa thông tin đầy đủ
        """
        return self.constraint_checker.check_schedule(schedule)
    
    def compare_individuals(self, schedule1: Schedule, schedule2: Schedule) -> int:
        """
        So sánh 2 cá thể
        
        Returns: 1 nếu schedule1 tốt hơn, -1 nếu schedule2 tốt hơn, 0 nếu bằng nhau
        """
        fitness1 = self.evaluate(schedule1)[0]
        fitness2 = self.evaluate(schedule2)[0]
        
        if fitness1 > fitness2:
            return 1
        elif fitness1 < fitness2:
            return -1
        else:
            return 0
    
    def get_best_individual(self, population: List[Schedule]) -> Schedule:
        """
        Tìm cá thể tốt nhất trong quần thể
        
        Returns: Schedule tốt nhất
        """
        best = None
        best_fitness = float('-inf')
        
        for schedule in population:
            fitness = self.evaluate(schedule)[0]
            if fitness > best_fitness:
                best_fitness = fitness
                best = schedule
        
        return best
    
    def get_population_statistics(self, population: List[Schedule]) -> Dict:
        """
        Tính thống kê về quần thể
        
        Returns: Dict chứa các thống kê
        """
        fitness_scores = [self.evaluate(s)[0] for s in population]
        
        valid_count = 0
        for schedule in population:
            if self.constraint_checker.is_schedule_valid(schedule):
                valid_count += 1
        
        stats = {
            'population_size': len(population),
            'best_fitness': max(fitness_scores),
            'worst_fitness': min(fitness_scores),
            'avg_fitness': sum(fitness_scores) / len(fitness_scores),
            'valid_schedules': valid_count,
            'valid_percentage': (valid_count / len(population)) * 100
        }
        
        return stats
    
    def print_population_statistics(self, population: List[Schedule], generation: int = 0):
        """
        In thống kê quần thể
        """
        stats = self.get_population_statistics(population)
        
        print("=" * 70)
        print(f"THỐNG KÊ QUẦN THỂ - Thế hệ {generation}")
        print("=" * 70)
        print(f"Kích thước quần thể: {stats['population_size']}")
        print(f"Số lịch hợp lệ: {stats['valid_schedules']} ({stats['valid_percentage']:.1f}%)")
        print(f"Fitness tốt nhất: {stats['best_fitness']:.2f}")
        print(f"Fitness trung bình: {stats['avg_fitness']:.2f}")
        print(f"Fitness tệ nhất: {stats['worst_fitness']:.2f}")
        print("=" * 70)
    
    def is_valid_schedule(self, schedule: Schedule) -> bool:
        """
        Kiểm tra nhanh xem lịch có hợp lệ không
        
        Returns: True nếu không vi phạm hard constraints
        """
        return self.constraint_checker.is_schedule_valid(schedule)
    
    def get_violation_summary(self, schedule: Schedule) -> str:
        """
        Lấy tóm tắt các vi phạm
        
        Returns: String mô tả các vi phạm
        """
        result = self.constraint_checker.check_schedule(schedule)
        
        if result['is_valid']:
            return "✓ Lịch hợp lệ - Không có vi phạm hard constraints"
        
        violations = []
        for constraint_name, (is_valid, count) in result['hard_constraints']['details'].items():
            if not is_valid:
                violations.append(f"{constraint_name}: {count} vi phạm")
        
        return "✗ Vi phạm: " + ", ".join(violations)
    
    def calculate_diversity(self, population: List[Schedule]) -> float:
        """
        Tính độ đa dạng của quần thể
        
        Diversity cao = quần thể có nhiều giải pháp khác nhau
        Diversity thấp = quần thể hội tụ về một điểm
        
        Returns: Diversity score (0-100)
        """
        if len(population) < 2:
            return 0.0
        
        fitness_scores = [self.evaluate(s)[0] for s in population]
        
        # Tính standard deviation của fitness
        avg_fitness = sum(fitness_scores) / len(fitness_scores)
        variance = sum((f - avg_fitness) ** 2 for f in fitness_scores) / len(fitness_scores)
        std_dev = variance ** 0.5
        
        # Normalize về 0-100
        # Giả sử std_dev lớn (>50) là diversity cao
        diversity = min(100, (std_dev / 50) * 100)
        
        return diversity