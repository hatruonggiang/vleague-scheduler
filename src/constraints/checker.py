from typing import Dict, List, Tuple
from ..models.schedule import Schedule
from ..models.team import Team
from .hard_constraints import HardConstraints
from .soft_constraints import SoftConstraints

class ConstraintChecker:
    """
    Tổng hợp kiểm tra tất cả các ràng buộc (hard và soft)
    """
    
    def __init__(self, teams: List[Team], 
                 distances: Dict[Tuple[str, str], float],
                 shared_stadiums: Dict[int, List[int]],
                 derby_pairs: List[Tuple[int, int]] = None,
                 soft_weights: Dict[str, float] = None):
        """
        Args:
            teams: Danh sách đội bóng
            distances: Ma trận khoảng cách
            shared_stadiums: Dict các sân dùng chung
            derby_pairs: List các cặp derby
            soft_weights: Trọng số các ràng buộc mềm
        """
        self.teams = teams
        self.teams_dict = {team.id: team for team in teams}
        self.distances = distances
        self.shared_stadiums = shared_stadiums
        self.derby_pairs = derby_pairs or []
        self.soft_weights = soft_weights
        
        # Khởi tạo checkers
        self.hard_checker = HardConstraints(teams)
        self.soft_checker = SoftConstraints(teams, distances)
    
    def check_schedule(self, schedule: Schedule) -> Dict:
        """
        Kiểm tra toàn bộ lịch thi đấu
        
        Returns: Dict chứa kết quả kiểm tra đầy đủ
        """
        # Kiểm tra hard constraints
        hard_valid, hard_results = self.hard_checker.check_all_hard_constraints(
            schedule, self.shared_stadiums, self.teams_dict
        )
        total_hard_violations = self.hard_checker.get_total_violations(hard_results)
        
        # Kiểm tra soft constraints
        soft_results = self.soft_checker.evaluate_all_soft_constraints(
            schedule, self.derby_pairs
        )
        soft_score = self.soft_checker.get_weighted_score(soft_results, self.soft_weights)
        
        # Tổng hợp kết quả
        result = {
            'is_valid': hard_valid,
            'hard_constraints': {
                'valid': hard_valid,
                'total_violations': total_hard_violations,
                'details': hard_results
            },
            'soft_constraints': {
                'weighted_score': soft_score,
                'details': soft_results
            },
            'overall_score': self._calculate_overall_score(
                hard_valid, total_hard_violations, soft_score
            )
        }
        
        return result
    
    def _calculate_overall_score(self, hard_valid: bool, 
                                 hard_violations: int, 
                                 soft_score: float) -> float:
        """
        Tính điểm tổng thể cho lịch thi đấu
        
        Nếu vi phạm hard constraints thì điểm rất thấp
        Nếu không vi phạm thì điểm = soft_score
        
        Returns: Score (0-100)
        """
        if hard_valid:
            return soft_score
        else:
            # Phạt nặng cho mỗi vi phạm hard constraint
            penalty = hard_violations * 10
            return max(0, soft_score - penalty)
    
    def is_schedule_valid(self, schedule: Schedule) -> bool:
        """
        Kiểm tra nhanh xem lịch có hợp lệ không (chỉ hard constraints)
        
        Returns: True nếu không vi phạm hard constraints
        """
        hard_valid, _ = self.hard_checker.check_all_hard_constraints(
            schedule, self.shared_stadiums, self.teams_dict
        )
        return hard_valid
    
    def get_fitness_score(self, schedule: Schedule) -> float:
        """
        Tính fitness score cho GA (kết hợp hard và soft)
        
        Returns: Fitness score (càng cao càng tốt)
        """
        result = self.check_schedule(schedule)
        return result['overall_score']
    
    def print_report(self, schedule: Schedule) -> None:
        """
        In báo cáo chi tiết về lịch thi đấu
        """
        result = self.check_schedule(schedule)
        
        print("=" * 70)
        print("BÁO CÁO ĐÁNH GIÁ LỊCH THI ĐẤU")
        print("=" * 70)
        
        # Hard constraints
        print("\n1. RÀNG BUỘC CỨNG (HARD CONSTRAINTS):")
        print(f"   Trạng thái: {'✓ HỢP LỆ' if result['hard_constraints']['valid'] else '✗ VI PHẠM'}")
        print(f"   Tổng vi phạm: {result['hard_constraints']['total_violations']}")
        print("\n   Chi tiết:")
        
        for constraint_name, (is_valid, violations) in result['hard_constraints']['details'].items():
            status = "✓" if is_valid else "✗"
            print(f"   {status} {constraint_name}: {violations} vi phạm")
        
        # Soft constraints
        print("\n2. RÀNG BUỘC MỀM (SOFT CONSTRAINTS):")
        print(f"   Điểm tổng (có trọng số): {result['soft_constraints']['weighted_score']:.2f}/100")
        print("\n   Chi tiết:")
        
        for constraint_name, score in result['soft_constraints']['details'].items():
            bar_length = int(score / 5)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"   {constraint_name:25s}: {bar} {score:5.1f}/100")
        
        # Overall
        print("\n" + "=" * 70)
        print(f"ĐIỂM TỔNG THỂ: {result['overall_score']:.2f}/100")
        print("=" * 70)
    
    def get_violation_details(self, schedule: Schedule) -> Dict:
        """
        Lấy chi tiết các vi phạm để debug hoặc repair
        
        Returns: Dict chứa thông tin chi tiết các vi phạm
        """
        violations = {
            'hard': [],
            'soft': []
        }
        
        # Hard constraints violations
        hard_valid, hard_results = self.hard_checker.check_all_hard_constraints(
            schedule, self.shared_stadiums, self.teams_dict
        )
        
        for constraint_name, (is_valid, count) in hard_results.items():
            if not is_valid:
                violations['hard'].append({
                    'constraint': constraint_name,
                    'violations_count': count
                })
        
        # Soft constraints low scores
        soft_results = self.soft_checker.evaluate_all_soft_constraints(
            schedule, self.derby_pairs
        )
        
        for constraint_name, score in soft_results.items():
            if score < 50:  # Điểm dưới 50 coi là cần cải thiện
                violations['soft'].append({
                    'constraint': constraint_name,
                    'score': score
                })
        
        return violations
    
    def compare_schedules(self, schedules: List[Schedule]) -> None:
        """
        So sánh nhiều lịch thi đấu
        
        Args:
            schedules: List các lịch cần so sánh
        """
        print("=" * 70)
        print("SO SÁNH CÁC LỊCH THI ĐẤU")
        print("=" * 70)
        
        results = []
        for i, schedule in enumerate(schedules, 1):
            result = self.check_schedule(schedule)
            results.append({
                'index': i,
                'valid': result['is_valid'],
                'hard_violations': result['hard_constraints']['total_violations'],
                'soft_score': result['soft_constraints']['weighted_score'],
                'overall_score': result['overall_score']
            })
        
        # In bảng so sánh
        print(f"\n{'#':<5} {'Valid':<8} {'Hard Vio.':<12} {'Soft Score':<12} {'Overall':<12}")
        print("-" * 70)
        
        for r in results:
            valid_str = "✓" if r['valid'] else "✗"
            print(f"{r['index']:<5} {valid_str:<8} {r['hard_violations']:<12} "
                  f"{r['soft_score']:<12.2f} {r['overall_score']:<12.2f}")
        
        # Tìm lịch tốt nhất
        best = max(results, key=lambda x: x['overall_score'])
        print("-" * 70)
        print(f"Lịch tốt nhất: #{best['index']} (Overall Score: {best['overall_score']:.2f})")
        print("=" * 70)