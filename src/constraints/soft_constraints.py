from typing import List, Dict, Tuple
from ..models.schedule import Schedule
from ..models.team import Team

class SoftConstraints:
    """
    Các ràng buộc mềm - NÊN thỏa mãn nhưng có thể linh hoạt
    """
    
    def __init__(self, teams: List[Team], distances: Dict[Tuple[str, str], float]):
        self.teams = teams
        self.distances = distances
        self.team_ids = [team.id for team in teams]
        self.teams_dict = {team.id: team for team in teams}
        self.n_teams = len(teams)
    
    def evaluate_home_away_balance(self, schedule: Schedule) -> float:
        """
        Đánh giá sự cân bằng home/away trong các giai đoạn của mùa giải
        
        Chia mùa giải thành các giai đoạn, kiểm tra mỗi đội không liên tục
        đá quá nhiều trận home hoặc away
        
        Returns: Score (càng cao càng tốt, 0-100)
        """
        score = 100.0
        penalty = 0
        
        # Kiểm tra từng đội
        for team_id in self.team_ids:
            team_matches = schedule.get_matches_by_team(team_id)
            team_matches_sorted = sorted(team_matches, key=lambda m: m.round_number)
            
            # Kiểm tra chuỗi home/away liên tiếp
            consecutive_home = 0
            consecutive_away = 0
            max_consecutive_home = 0
            max_consecutive_away = 0
            
            for match in team_matches_sorted:
                if match.home_team_id == team_id:
                    consecutive_home += 1
                    consecutive_away = 0
                    max_consecutive_home = max(max_consecutive_home, consecutive_home)
                else:
                    consecutive_away += 1
                    consecutive_home = 0
                    max_consecutive_away = max(max_consecutive_away, consecutive_away)
            
            # Phạt nếu quá nhiều trận liên tiếp
            if max_consecutive_home > 3:
                penalty += (max_consecutive_home - 3) * 5
            if max_consecutive_away > 3:
                penalty += (max_consecutive_away - 3) * 5
        
        score = max(0, score - penalty)
        return score
    
    def evaluate_travel_distance(self, schedule: Schedule) -> float:
        """
        Đánh giá tổng quãng đường di chuyển của tất cả các đội
        
        Returns: Score (càng cao càng tốt, 0-100)
        """
        total_distance = 0.0
        
        for team_id in self.team_ids:
            team = self.teams_dict[team_id]
            team_matches = schedule.get_matches_by_team(team_id)
            team_matches_sorted = sorted(team_matches, key=lambda m: m.round_number)
            
            # Tính khoảng cách di chuyển cho đội này
            for match in team_matches_sorted:
                # Nếu đá sân khách, tính khoảng cách từ thành phố của đội đến sân đấu
                if match.away_team_id == team_id:
                    home_team = self.teams_dict[match.home_team_id]
                    distance = self.distances.get((team.city, home_team.city), 0)
                    total_distance += distance * 2  # Cả đi lẫn về
        
        # Normalize: giả sử khoảng cách trung bình mỗi trận away là 500km
        # Tổng trận away của tất cả đội: 14 * 13 = 182 trận (mỗi đội 13 trận away)
        # Tổng khoảng cách dự kiến: 182 * 500 * 2 = 182,000 km
        expected_distance = 182000
        
        # Score giảm dần khi khoảng cách tăng
        if total_distance <= expected_distance:
            score = 100.0
        else:
            # Phạt nếu vượt quá khoảng cách dự kiến
            excess_ratio = (total_distance - expected_distance) / expected_distance
            score = max(0, 100 - excess_ratio * 50)
        
        return score
    
    def evaluate_competitive_balance(self, schedule: Schedule) -> float:
        """
        Đánh giá sự cân bằng độ khó trong lịch thi đấu
        
        Tránh trường hợp một đội phải gặp nhiều đối thủ mạnh liên tiếp
        hoặc nhiều đội yếu liên tiếp
        
        Note: Cần có ranking/strength của các đội để đánh giá chính xác
        Hiện tại chỉ đánh giá phân bố đối thủ
        
        Returns: Score (càng cao càng tốt, 0-100)
        """
        score = 100.0
        
        # Đơn giản hóa: kiểm tra đội không gặp cùng một nhóm đội liên tiếp
        # (VD: các đội cùng khu vực)
        
        # Nhóm đội theo khu vực
        regions = {}
        for team in self.teams:
            region = self._get_region(team.city)
            if region not in regions:
                regions[region] = []
            regions[region].append(team.id)
        
        penalty = 0
        
        for team_id in self.team_ids:
            team_matches = schedule.get_matches_by_team(team_id)
            team_matches_sorted = sorted(team_matches, key=lambda m: m.round_number)
            
            # Kiểm tra không gặp quá nhiều đội cùng khu vực liên tiếp
            for i in range(len(team_matches_sorted) - 2):
                opponents = []
                for j in range(3):  # Kiểm tra 3 trận liên tiếp
                    match = team_matches_sorted[i + j]
                    opponent_id = match.away_team_id if match.home_team_id == team_id else match.home_team_id
                    opponents.append(opponent_id)
                
                # Kiểm tra các đối thủ có cùng khu vực không
                opponent_regions = [self._get_region(self.teams_dict[opp].city) for opp in opponents]
                if len(set(opponent_regions)) == 1:  # Cả 3 đối thủ cùng khu vực
                    penalty += 5
        
        score = max(0, score - penalty)
        return score
    
    def _get_region(self, city: str) -> str:
        """
        Phân loại thành phố theo khu vực
        """
        north = ['Hà Nội', 'Nam Định', 'Hải Phòng']
        central = ['Hà Tĩnh', 'Vinh', 'Đà Nẵng', 'Tam Kỳ', 'Quy Nhơn']
        south = ['Pleiku', 'Nha Trang', 'TP.HCM', 'Thủ Dầu Một']
        
        if city in north:
            return 'North'
        elif city in central:
            return 'Central'
        elif city in south:
            return 'South'
        else:
            return 'Unknown'
    
    def evaluate_derby_distribution(self, schedule: Schedule, 
                                    derby_pairs: List[Tuple[int, int]]) -> float:
        """
        Đánh giá sự phân bố các trận derby trong mùa giải
        
        Các trận derby nên được phân bố đều, không quá tập trung
        
        Args:
            derby_pairs: List các cặp đội derby, VD: [(1, 2), (1, 3)]
        
        Returns: Score (càng cao càng tốt, 0-100)
        """
        if not derby_pairs:
            return 100.0
        
        score = 100.0
        
        # Tìm các trận derby trong lịch
        derby_rounds = []
        
        for match in schedule.matches:
            pair = tuple(sorted([match.home_team_id, match.away_team_id]))
            if pair in derby_pairs or (pair[1], pair[0]) in derby_pairs:
                derby_rounds.append(match.round_number)
        
        if not derby_rounds:
            return score
        
        derby_rounds_sorted = sorted(derby_rounds)
        
        # Kiểm tra khoảng cách giữa các trận derby
        for i in range(len(derby_rounds_sorted) - 1):
            gap = derby_rounds_sorted[i + 1] - derby_rounds_sorted[i]
            
            # Phạt nếu các trận derby quá gần nhau
            if gap < 3:
                score -= 10
        
        return max(0, score)
    
    def evaluate_rest_days_fairness(self, schedule: Schedule) -> float:
        """
        Đánh giá sự công bằng về ngày nghỉ giữa các trận
        
        Các đội nên có số ngày nghỉ tương đương nhau
        
        Returns: Score (càng cao càng tốt, 0-100)
        """
        # Note: Cần có thông tin về ngày thi đấu cụ thể
        # Hiện tại chỉ kiểm tra phân bố vòng đấu
        
        score = 100.0
        
        # Kiểm tra mỗi đội có trận đấu đều đặn qua các vòng
        for team_id in self.team_ids:
            team_matches = schedule.get_matches_by_team(team_id)
            rounds = sorted([m.round_number for m in team_matches])
            
            # Kiểm tra có vòng nào bị bỏ sót không
            for i in range(len(rounds) - 1):
                gap = rounds[i + 1] - rounds[i]
                if gap > 1:
                    # Đội này bỏ sót vòng (có thể do lỗi lịch)
                    score -= 5
        
        return max(0, score)
    
    def evaluate_all_soft_constraints(self, schedule: Schedule,
                                     derby_pairs: List[Tuple[int, int]] = None) -> Dict[str, float]:
        """
        Đánh giá tất cả ràng buộc mềm
        
        Returns: Dict với key là tên constraint, value là score
        """
        results = {}
        
        results['home_away_balance'] = self.evaluate_home_away_balance(schedule)
        results['travel_distance'] = self.evaluate_travel_distance(schedule)
        results['competitive_balance'] = self.evaluate_competitive_balance(schedule)
        results['rest_days_fairness'] = self.evaluate_rest_days_fairness(schedule)
        
        if derby_pairs:
            results['derby_distribution'] = self.evaluate_derby_distribution(schedule, derby_pairs)
        
        return results
    
    def get_weighted_score(self, results: Dict[str, float], 
                          weights: Dict[str, float] = None) -> float:
        """
        Tính tổng điểm có trọng số
        
        Args:
            results: Dict các scores
            weights: Dict các trọng số (nếu None sử dụng mặc định)
        
        Returns: Weighted score
        """
        if weights is None:
            weights = {
                'home_away_balance': 0.25,
                'travel_distance': 0.30,
                'competitive_balance': 0.20,
                'rest_days_fairness': 0.15,
                'derby_distribution': 0.10
            }
        
        total_score = 0.0
        total_weight = 0.0
        
        for key, score in results.items():
            if key in weights:
                total_score += score * weights[key]
                total_weight += weights[key]
        
        # Normalize về thang 0-100
        if total_weight > 0:
            return total_score / total_weight
        else:
            return 0.0