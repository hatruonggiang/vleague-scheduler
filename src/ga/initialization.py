import random
from typing import List, Set, Tuple
from ..models.team import Team
from ..models.match import Match
from ..models.schedule import Schedule
from .encoding import ScheduleEncoding

class PopulationInitializer:
    """
    Khởi tạo quần thể ban đầu cho GA
    """
    
    def __init__(self, teams: List[Team], shared_stadiums: dict):
        self.teams = teams
        self.shared_stadiums = shared_stadiums
        self.encoding = ScheduleEncoding(teams)
        self.n_teams = len(teams)
        self.total_rounds = self.encoding.total_rounds
        self.matches_per_round = self.encoding.matches_per_round
        
    def create_random_schedule(self) -> Schedule:
        """
        Tạo một lịch thi đấu ngẫu nhiên
        
        Strategy: 
        1. Tạo tất cả các trận đấu
        2. Shuffle và phân vào các vòng
        3. Đảm bảo mỗi đội chỉ đá 1 trận/vòng
        """
        all_matches = self.encoding.create_all_possible_matches()
        random.shuffle(all_matches)
        
        schedule = Schedule()
        round_num = 1
        teams_in_round = set()
        round_match_count = 0
        
        for match in all_matches:
            # Kiểm tra đội đã đá trong vòng này chưa
            if (match.home_team_id not in teams_in_round and 
                match.away_team_id not in teams_in_round):
                
                # Gán vòng cho trận đấu
                new_match = Match(
                    id=match.id,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    stadium_id=match.stadium_id,
                    round_number=round_num
                )
                schedule.add_match(new_match)
                
                teams_in_round.add(match.home_team_id)
                teams_in_round.add(match.away_team_id)
                round_match_count += 1
                
                # Chuyển sang vòng mới nếu đủ số trận
                if round_match_count == self.matches_per_round:
                    round_num += 1
                    teams_in_round = set()
                    round_match_count = 0
        
        return schedule
    
    def create_round_robin_schedule(self) -> Schedule:
        """
        Tạo lịch theo thuật toán Round-robin chuẩn
        
        Đây là phương pháp tạo lịch có cấu trúc tốt
        """
        schedule = Schedule()
        
        # Tạo lượt đi (13 vòng đầu)
        first_leg_rounds = self.encoding.create_round_robin_groups(self.teams)
        
        match_id = 1
        for round_num, round_pairs in enumerate(first_leg_rounds, 1):
            for home_id, away_id in round_pairs:
                home_team = next(t for t in self.teams if t.id == home_id)
                
                match = Match(
                    id=match_id,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    stadium_id=home_team.home_stadium_id,
                    round_number=round_num
                )
                schedule.add_match(match)
                match_id += 1
        
        # Tạo lượt về (13 vòng sau) - đảo home/away
        for round_num, round_pairs in enumerate(first_leg_rounds, 14):
            for home_id, away_id in round_pairs:
                # Đảo home và away
                away_team = next(t for t in self.teams if t.id == away_id)
                
                match = Match(
                    id=match_id,
                    home_team_id=away_id,  # Đảo
                    away_team_id=home_id,  # Đảo
                    stadium_id=away_team.home_stadium_id,
                    round_number=round_num
                )
                schedule.add_match(match)
                match_id += 1
        
        return schedule
    
    def create_balanced_schedule(self) -> Schedule:
        """
        Tạo lịch cân bằng home/away theo từng giai đoạn
        
        Strategy: Đảm bảo trong mỗi 4 vòng, mỗi đội có ~2 trận home và ~2 trận away
        """
        all_matches = self.encoding.create_all_possible_matches()
        
        # Phân loại trận theo đội
        team_home_matches = {t.id: [] for t in self.teams}
        team_away_matches = {t.id: [] for t in self.teams}
        
        for match in all_matches:
            team_home_matches[match.home_team_id].append(match)
            team_away_matches[match.away_team_id].append(match)
        
        # Shuffle
        for team_id in team_home_matches:
            random.shuffle(team_home_matches[team_id])
            random.shuffle(team_away_matches[team_id])
        
        schedule = Schedule()
        round_num = 1
        
        # Luân phiên home/away
        while round_num <= self.total_rounds:
            teams_in_round = set()
            round_matches = []
            
            # Ưu tiên home cho nửa số đội, away cho nửa còn lại
            available_teams = [t.id for t in self.teams]
            random.shuffle(available_teams)
            
            home_priority = set(available_teams[:self.n_teams//2])
            
            # Thử thêm trận vào vòng
            for team_id in available_teams:
                if team_id in teams_in_round:
                    continue
                
                # Chọn trận home hoặc away
                if team_id in home_priority and team_home_matches[team_id]:
                    match = team_home_matches[team_id].pop(0)
                elif team_away_matches[team_id]:
                    match = team_away_matches[team_id].pop(0)
                elif team_home_matches[team_id]:
                    match = team_home_matches[team_id].pop(0)
                else:
                    continue
                
                opponent_id = match.away_team_id if match.home_team_id == team_id else match.home_team_id
                
                if opponent_id not in teams_in_round:
                    new_match = Match(
                        id=match.id,
                        home_team_id=match.home_team_id,
                        away_team_id=match.away_team_id,
                        stadium_id=match.stadium_id,
                        round_number=round_num
                    )
                    round_matches.append(new_match)
                    teams_in_round.add(team_id)
                    teams_in_round.add(opponent_id)
            
            # Thêm vào schedule
            for match in round_matches:
                schedule.add_match(match)
            
            round_num += 1
        
        return schedule
    
    def create_stadium_aware_schedule(self) -> Schedule:
        """
        Tạo lịch tránh xung đột sân dùng chung
        
        Ưu tiên không để các đội dùng chung sân đá home cùng vòng
        """
        all_matches = self.encoding.create_all_possible_matches()
        random.shuffle(all_matches)
        
        schedule = Schedule()
        round_num = 1
        
        while round_num <= self.total_rounds:
            teams_in_round = set()
            stadiums_in_round = set()
            round_matches = []
            
            for match in all_matches[:]:
                # Kiểm tra xung đột đội
                if (match.home_team_id in teams_in_round or 
                    match.away_team_id in teams_in_round):
                    continue
                
                # Kiểm tra xung đột sân (cho các sân dùng chung)
                if match.stadium_id in self.shared_stadiums:
                    if match.stadium_id in stadiums_in_round:
                        continue
                
                # Thêm trận vào vòng
                new_match = Match(
                    id=match.id,
                    home_team_id=match.home_team_id,
                    away_team_id=match.away_team_id,
                    stadium_id=match.stadium_id,
                    round_number=round_num
                )
                round_matches.append(new_match)
                teams_in_round.add(match.home_team_id)
                teams_in_round.add(match.away_team_id)
                stadiums_in_round.add(match.stadium_id)
                
                all_matches.remove(match)
                
                if len(round_matches) == self.matches_per_round:
                    break
            
            # Thêm vào schedule
            for match in round_matches:
                schedule.add_match(match)
            
            round_num += 1
        
        return schedule
    
    def initialize_population(self, population_size: int, 
                            strategies: dict = None) -> List[Schedule]:
        """
        Khởi tạo quần thể với nhiều chiến lược khác nhau
        
        Args:
            population_size: Kích thước quần thể
            strategies: Dict tỉ lệ các chiến lược, VD: {
                'random': 0.4,
                'round_robin': 0.2,
                'balanced': 0.2,
                'stadium_aware': 0.2
            }
        
        Returns: List các Schedule
        """
        if strategies is None:
            strategies = {
                'random': 0.4,
                'round_robin': 0.2,
                'balanced': 0.2,
                'stadium_aware': 0.2
            }
        
        population = []
        
        # Tính số lượng cá thể cho mỗi chiến lược
        n_random = int(population_size * strategies.get('random', 0))
        n_round_robin = int(population_size * strategies.get('round_robin', 0))
        n_balanced = int(population_size * strategies.get('balanced', 0))
        n_stadium_aware = population_size - n_random - n_round_robin - n_balanced
        
        # Tạo các cá thể
        print(f"Khởi tạo quần thể: {population_size} cá thể")
        
        for i in range(n_random):
            schedule = self.create_random_schedule()
            population.append(schedule)
            if (i + 1) % 10 == 0:
                print(f"  Random: {i + 1}/{n_random}")
        
        for i in range(n_round_robin):
            schedule = self.create_round_robin_schedule()
            population.append(schedule)
            print(f"  Round-robin: {i + 1}/{n_round_robin}")
        
        for i in range(n_balanced):
            schedule = self.create_balanced_schedule()
            population.append(schedule)
            if (i + 1) % 5 == 0:
                print(f"  Balanced: {i + 1}/{n_balanced}")
        
        for i in range(n_stadium_aware):
            schedule = self.create_stadium_aware_schedule()
            population.append(schedule)
            if (i + 1) % 5 == 0:
                print(f"  Stadium-aware: {i + 1}/{n_stadium_aware}")
        
        print(f"Hoàn thành khởi tạo {len(population)} cá thể")
        
        return population