from typing import List, Set, Tuple
from ..models.schedule import Schedule
from ..models.team import Team

class HardConstraints:
    """
    Các ràng buộc cứng - BẮT BUỘC phải thỏa mãn
    """
    
    def __init__(self, teams: List[Team]):
        self.teams = teams
        self.team_ids = [team.id for team in teams]
        self.n_teams = len(teams)
        self.total_rounds = 2 * (self.n_teams - 1)  # 26 vòng cho 14 đội
    
    def check_all_matchups_exist(self, schedule: Schedule) -> Tuple[bool, int]:
        """
        Kiểm tra mỗi cặp đội phải gặp nhau đúng 2 lần (1 home, 1 away)
        
        Returns: (is_valid, violations_count)
        """
        violations = 0
        
        # Tạo dictionary đếm số lần gặp nhau
        matchup_count = {}
        
        for match in schedule.matches:
            key = (match.home_team_id, match.away_team_id)
            matchup_count[key] = matchup_count.get(key, 0) + 1
        
        # Kiểm tra mỗi cặp đội
        for i in range(self.n_teams):
            for j in range(self.n_teams):
                if i != j:
                    team_i = self.team_ids[i]
                    team_j = self.team_ids[j]
                    key = (team_i, team_j)
                    
                    count = matchup_count.get(key, 0)
                    if count != 1:
                        violations += abs(count - 1)
        
        return (violations == 0, violations)
    
    def check_no_consecutive_same_opponent(self, schedule: Schedule) -> Tuple[bool, int]:
        """
        Kiểm tra 2 đội không được gặp nhau ở 2 vòng liên tiếp
        
        Returns: (is_valid, violations_count)
        """
        violations = 0
        
        # Group matches by round
        rounds = {}
        for match in schedule.matches:
            if match.round_number not in rounds:
                rounds[match.round_number] = []
            rounds[match.round_number].append(match)
        
        # Kiểm tra các vòng liên tiếp
        for round_num in range(1, self.total_rounds):
            if round_num not in rounds or (round_num + 1) not in rounds:
                continue
            
            current_round = rounds[round_num]
            next_round = rounds[round_num + 1]
            
            # Tạo set các cặp đấu trong vòng hiện tại
            current_matchups = set()
            for match in current_round:
                pair = tuple(sorted([match.home_team_id, match.away_team_id]))
                current_matchups.add(pair)
            
            # Kiểm tra vòng tiếp theo
            for match in next_round:
                pair = tuple(sorted([match.home_team_id, match.away_team_id]))
                if pair in current_matchups:
                    violations += 1
        
        return (violations == 0, violations)
    
    def check_one_match_per_team_per_round(self, schedule: Schedule) -> Tuple[bool, int]:
        """
        Kiểm tra mỗi đội chỉ đá đúng 1 trận mỗi vòng
        
        Returns: (is_valid, violations_count)
        """
        violations = 0
        
        # Group matches by round
        rounds = {}
        for match in schedule.matches:
            if match.round_number not in rounds:
                rounds[match.round_number] = []
            rounds[match.round_number].append(match)
        
        # Kiểm tra mỗi vòng
        for round_num, matches in rounds.items():
            team_match_count = {team_id: 0 for team_id in self.team_ids}
            
            for match in matches:
                team_match_count[match.home_team_id] += 1
                team_match_count[match.away_team_id] += 1
            
            # Đếm vi phạm
            for team_id, count in team_match_count.items():
                if count != 1:
                    violations += abs(count - 1)
        
        return (violations == 0, violations)
    
    def check_shared_stadium_conflict(self, schedule: Schedule, 
                                     shared_stadiums: dict) -> Tuple[bool, int]:
        """
        Kiểm tra các đội dùng chung sân không đá sân nhà cùng vòng
        
        Args:
            shared_stadiums: Dict {stadium_id: [team_ids]}
        
        Returns: (is_valid, violations_count)
        """
        violations = 0
        
        if not shared_stadiums:
            return (True, 0)
        
        # Group matches by round
        rounds = {}
        for match in schedule.matches:
            if match.round_number not in rounds:
                rounds[match.round_number] = []
            rounds[match.round_number].append(match)
        
        # Kiểm tra mỗi vòng
        for round_num, matches in rounds.items():
            # Đếm số trận sân nhà tại mỗi sân
            stadium_usage = {}
            
            for match in matches:
                stadium_id = match.stadium_id
                if stadium_id not in stadium_usage:
                    stadium_usage[stadium_id] = []
                stadium_usage[stadium_id].append(match.home_team_id)
            
            # Kiểm tra các sân dùng chung
            for stadium_id, teams_using in stadium_usage.items():
                if stadium_id in shared_stadiums and len(teams_using) > 1:
                    violations += len(teams_using) - 1
        
        return (violations == 0, violations)
    
    def check_correct_home_stadium(self, schedule: Schedule, 
                                   teams_dict: dict) -> Tuple[bool, int]:
        """
        Kiểm tra mỗi đội đá sân nhà đúng sân của mình
        
        Args:
            teams_dict: Dict {team_id: Team}
        
        Returns: (is_valid, violations_count)
        """
        violations = 0
        
        for match in schedule.matches:
            home_team = teams_dict[match.home_team_id]
            if match.stadium_id != home_team.home_stadium_id:
                violations += 1
        
        return (violations == 0, violations)
    
    def check_total_matches(self, schedule: Schedule) -> Tuple[bool, int]:
        """
        Kiểm tra tổng số trận đúng bằng n*(n-1)
        
        Returns: (is_valid, violations_count)
        """
        expected_matches = self.n_teams * (self.n_teams - 1)
        actual_matches = len(schedule.matches)
        violations = abs(expected_matches - actual_matches)
        
        return (violations == 0, violations)
    
    def check_matches_per_round(self, schedule: Schedule) -> Tuple[bool, int]:
        """
        Kiểm tra mỗi vòng có đúng n/2 trận
        
        Returns: (is_valid, violations_count)
        """
        violations = 0
        expected_per_round = self.n_teams // 2
        
        # Group matches by round
        rounds = {}
        for match in schedule.matches:
            if match.round_number not in rounds:
                rounds[match.round_number] = []
            rounds[match.round_number].append(match)
        
        for round_num, matches in rounds.items():
            if len(matches) != expected_per_round:
                violations += abs(len(matches) - expected_per_round)
        
        return (violations == 0, violations)
    
    def check_all_hard_constraints(self, schedule: Schedule, 
                                   shared_stadiums: dict,
                                   teams_dict: dict) -> Tuple[bool, dict]:
        """
        Kiểm tra tất cả ràng buộc cứng
        
        Returns: (is_valid, violations_dict)
        """
        results = {}
        
        results['all_matchups'] = self.check_all_matchups_exist(schedule)
        results['no_consecutive'] = self.check_no_consecutive_same_opponent(schedule)
        results['one_match_per_round'] = self.check_one_match_per_team_per_round(schedule)
        results['stadium_conflict'] = self.check_shared_stadium_conflict(schedule, shared_stadiums)
        results['correct_stadium'] = self.check_correct_home_stadium(schedule, teams_dict)
        results['total_matches'] = self.check_total_matches(schedule)
        results['matches_per_round'] = self.check_matches_per_round(schedule)
        
        # Kiểm tra có vi phạm nào không
        is_valid = all(result[0] for result in results.values())
        
        return (is_valid, results)
    
    def get_total_violations(self, results: dict) -> int:
        """
        Tính tổng số vi phạm từ kết quả kiểm tra
        """
        return sum(result[1] for result in results.values())