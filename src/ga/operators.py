import random
from typing import List, Tuple
from ..models.schedule import Schedule
from ..models.match import Match
from ..models.team import Team

class GeneticOperators:
    """
    Các toán tử di truyền: Crossover và Mutation
    """
    
    def __init__(self, teams: List[Team]):
        self.teams = teams
        self.n_teams = len(teams)
        self.total_rounds = 2 * (self.n_teams - 1)
        self.matches_per_round = self.n_teams // 2
    
    # ==================== CROSSOVER OPERATORS ====================
    
    def crossover_round_swap(self, parent1: Schedule, parent2: Schedule) -> Tuple[Schedule, Schedule]:
        """
        Round Swap Crossover
        
        Chọn ngẫu nhiên một số vòng từ parent1, phần còn lại từ parent2
        
        Returns: (offspring1, offspring2)
        """
        # Chọn ngẫu nhiên các vòng để lấy từ parent1
        num_rounds_from_p1 = random.randint(1, self.total_rounds - 1)
        rounds_from_p1 = set(random.sample(range(1, self.total_rounds + 1), num_rounds_from_p1))
        
        offspring1 = Schedule()
        offspring2 = Schedule()
        
        # Offspring1: lấy một số vòng từ parent1, còn lại từ parent2
        used_matches_o1 = set()
        for match in parent1.matches:
            if match.round_number in rounds_from_p1:
                matchup = tuple(sorted([match.home_team_id, match.away_team_id]))
                if matchup not in used_matches_o1:
                    offspring1.add_match(match)
                    used_matches_o1.add(matchup)
        
        for match in parent2.matches:
            matchup = tuple(sorted([match.home_team_id, match.away_team_id]))
            if matchup not in used_matches_o1:
                offspring1.add_match(match)
                used_matches_o1.add(matchup)
        
        # Offspring2: ngược lại
        used_matches_o2 = set()
        for match in parent2.matches:
            if match.round_number in rounds_from_p1:
                matchup = tuple(sorted([match.home_team_id, match.away_team_id]))
                if matchup not in used_matches_o2:
                    offspring2.add_match(match)
                    used_matches_o2.add(matchup)
        
        for match in parent1.matches:
            matchup = tuple(sorted([match.home_team_id, match.away_team_id]))
            if matchup not in used_matches_o2:
                offspring2.add_match(match)
                used_matches_o2.add(matchup)
        
        return offspring1, offspring2
    
    def crossover_uniform(self, parent1: Schedule, parent2: Schedule) -> Tuple[Schedule, Schedule]:
        """
        Uniform Crossover
        
        Mỗi trận đấu được chọn ngẫu nhiên từ parent1 hoặc parent2
        
        Returns: (offspring1, offspring2)
        """
        offspring1 = Schedule()
        offspring2 = Schedule()
        
        # Tạo dict matchup -> match
        p1_matchups = {}
        p2_matchups = {}
        
        for match in parent1.matches:
            key = (match.home_team_id, match.away_team_id)
            p1_matchups[key] = match
        
        for match in parent2.matches:
            key = (match.home_team_id, match.away_team_id)
            p2_matchups[key] = match
        
        # Lấy tất cả matchups
        all_matchups = set(p1_matchups.keys()) | set(p2_matchups.keys())
        
        for matchup in all_matchups:
            if random.random() < 0.5:
                # Lấy từ parent1
                if matchup in p1_matchups:
                    offspring1.add_match(p1_matchups[matchup])
                if matchup in p2_matchups:
                    offspring2.add_match(p2_matchups[matchup])
            else:
                # Lấy từ parent2
                if matchup in p2_matchups:
                    offspring1.add_match(p2_matchups[matchup])
                if matchup in p1_matchups:
                    offspring2.add_match(p1_matchups[matchup])
        
        return offspring1, offspring2
    
    def crossover_single_point(self, parent1: Schedule, parent2: Schedule) -> Tuple[Schedule, Schedule]:
        """
        Single Point Crossover
        
        Chọn một điểm cắt (vòng đấu), phần trước lấy từ parent1, phần sau từ parent2
        
        Returns: (offspring1, offspring2)
        """
        cut_point = random.randint(1, self.total_rounds - 1)
        
        offspring1 = Schedule()
        offspring2 = Schedule()
        
        # Offspring1: vòng 1->cut_point từ parent1, phần còn lại từ parent2
        used_matchups_o1 = set()
        for match in parent1.matches:
            if match.round_number <= cut_point:
                matchup = tuple(sorted([match.home_team_id, match.away_team_id]))
                if matchup not in used_matchups_o1:
                    offspring1.add_match(match)
                    used_matchups_o1.add(matchup)
        
        for match in parent2.matches:
            matchup = tuple(sorted([match.home_team_id, match.away_team_id]))
            if matchup not in used_matchups_o1:
                offspring1.add_match(match)
                used_matchups_o1.add(matchup)
        
        # Offspring2: ngược lại
        used_matchups_o2 = set()
        for match in parent2.matches:
            if match.round_number <= cut_point:
                matchup = tuple(sorted([match.home_team_id, match.away_team_id]))
                if matchup not in used_matchups_o2:
                    offspring2.add_match(match)
                    used_matchups_o2.add(matchup)
        
        for match in parent1.matches:
            matchup = tuple(sorted([match.home_team_id, match.away_team_id]))
            if matchup not in used_matchups_o2:
                offspring2.add_match(match)
                used_matchups_o2.add(matchup)
        
        return offspring1, offspring2
    
    # ==================== MUTATION OPERATORS ====================
    
    def mutate_swap_matches(self, schedule: Schedule) -> Schedule:
        """
        Swap Matches Mutation
        
        Hoán đổi 2 trận đấu ngẫu nhiên
        
        Returns: Mutated schedule
        """
        mutated = schedule.clone()
        
        if len(mutated.matches) < 2:
            return mutated
        
        # Chọn 2 trận ngẫu nhiên
        idx1, idx2 = random.sample(range(len(mutated.matches)), 2)
        
        # Hoán đổi round_number
        temp_round = mutated.matches[idx1].round_number
        mutated.matches[idx1].round_number = mutated.matches[idx2].round_number
        mutated.matches[idx2].round_number = temp_round
        
        return mutated
    
    def mutate_swap_rounds(self, schedule: Schedule) -> Schedule:
        """
        Swap Rounds Mutation
        
        Hoán đổi tất cả trận đấu của 2 vòng
        
        Returns: Mutated schedule
        """
        mutated = schedule.clone()
        
        # Chọn 2 vòng ngẫu nhiên
        round1, round2 = random.sample(range(1, self.total_rounds + 1), 2)
        
        # Hoán đổi
        for match in mutated.matches:
            if match.round_number == round1:
                match.round_number = round2
            elif match.round_number == round2:
                match.round_number = round1
        
        return mutated
    
    def mutate_shuffle_round(self, schedule: Schedule) -> Schedule:
        """
        Shuffle Round Mutation
        
        Xáo trộn thứ tự các trận trong một vòng ngẫu nhiên
        (không làm thay đổi nhiều, chỉ để tạo diversity nhẹ)
        
        Returns: Mutated schedule
        """
        mutated = schedule.clone()
        
        # Chọn một vòng ngẫu nhiên
        target_round = random.randint(1, self.total_rounds)
        
        # Lấy các trận trong vòng đó
        round_matches = mutated.get_matches_by_round(target_round)
        
        if len(round_matches) > 1:
            # Shuffle (thực tế không làm thay đổi gì vì chỉ thay đổi thứ tự trong list)
            # Để có ý nghĩa hơn, ta có thể swap với trận ở vòng khác
            other_round = random.randint(1, self.total_rounds)
            if other_round != target_round:
                other_matches = mutated.get_matches_by_round(other_round)
                
                if round_matches and other_matches:
                    # Swap ngẫu nhiên 1 trận
                    match1 = random.choice(round_matches)
                    match2 = random.choice(other_matches)
                    
                    temp_round = match1.round_number
                    match1.round_number = match2.round_number
                    match2.round_number = temp_round
        
        return mutated
    
    def mutate_reverse_home_away(self, schedule: Schedule) -> Schedule:
        """
        Reverse Home/Away Mutation
        
        Đảo home/away của một trận ngẫu nhiên
        (Cần tìm và đảo cả trận lượt về tương ứng)
        
        Returns: Mutated schedule
        """
        mutated = schedule.clone()
        
        if not mutated.matches:
            return mutated
        
        # Chọn một trận ngẫu nhiên
        match_to_reverse = random.choice(mutated.matches)
        
        # Tìm trận lượt về (A-B <-> B-A)
        reverse_match = None
        for match in mutated.matches:
            if (match.home_team_id == match_to_reverse.away_team_id and
                match.away_team_id == match_to_reverse.home_team_id):
                reverse_match = match
                break
        
        if reverse_match:
            # Hoán đổi vòng đấu của 2 trận
            temp_round = match_to_reverse.round_number
            match_to_reverse.round_number = reverse_match.round_number
            reverse_match.round_number = temp_round
        
        return mutated
    
    def mutate_move_match(self, schedule: Schedule) -> Schedule:
        """
        Move Match Mutation
        
        Di chuyển một trận sang vòng khác
        
        Returns: Mutated schedule
        """
        mutated = schedule.clone()
        
        if not mutated.matches:
            return mutated
        
        # Chọn một trận
        match = random.choice(mutated.matches)
        
        # Chọn vòng mới
        new_round = random.randint(1, self.total_rounds)
        match.round_number = new_round
        
        return mutated
    
    def apply_mutation(self, schedule: Schedule, mutation_rate: float = 0.1) -> Schedule:
        """
        Áp dụng mutation với một mutation_rate
        
        Chọn ngẫu nhiên một trong các mutation operators
        
        Args:
            schedule: Schedule cần mutate
            mutation_rate: Xác suất mutate
        
        Returns: Mutated schedule (hoặc schedule gốc nếu không mutate)
        """
        if random.random() > mutation_rate:
            return schedule
        
        # Chọn ngẫu nhiên một mutation operator
        operators = [
            self.mutate_swap_matches,
            self.mutate_swap_rounds,
            self.mutate_shuffle_round,
            self.mutate_reverse_home_away,
            self.mutate_move_match
        ]
        
        mutation_func = random.choice(operators)
        return mutation_func(schedule)