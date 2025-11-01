#!/usr/bin/env python3
"""
Main entry point để chạy thử dự án V.League Scheduler
"""

import sys
from pathlib import Path

# Thêm src vào path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_processing.loader import DataLoader
from src.data_processing.validator import DataValidator
from src.data_processing.preprocessor import DataPreprocessor
from src.optimization.config import GAConfig
from src.optimization.ga_optimizer import GAOptimizer

def main():
    print("=" * 70)
    print("V.LEAGUE SCHEDULER - CHẠY THỬ")
    print("=" * 70)
    
    # Load data
    print("\n1. Load dữ liệu...")
    loader = DataLoader(data_dir="data/raw")
    
    teams = loader.load_teams()
    stadiums = loader.load_stadiums()
    distances = loader.load_distances()
    special_dates = loader.load_special_dates()
    
    print(f"   ✓ {len(teams)} đội")
    print(f"   ✓ {len(stadiums)} sân")
    print(f"   ✓ {len(distances)} khoảng cách")
    print(f"   ✓ {len(special_dates)} ngày đặc biệt")
    
    # Validate
    print("\n2. Validate dữ liệu...")
    validator = DataValidator()
    
    if validator.validate_all(teams, stadiums, distances, special_dates):
        print("   ✓ Dữ liệu hợp lệ")
    else:
        print("   ✗ Dữ liệu không hợp lệ:")
        for error in validator.get_errors():
            print(f"     - {error}")
        return
    
    # Preprocessing
    print("\n3. Tiền xử lý...")
    preprocessor = DataPreprocessor(teams, stadiums)
    shared_stadiums = preprocessor.get_teams_sharing_stadium()
    stats = preprocessor.get_statistics()
    
    print(f"   ✓ {stats['total_matches']} trận")
    print(f"   ✓ {stats['total_rounds']} vòng")
    print(f"   ✓ {stats['matches_per_round']} trận/vòng")
    
    # Config GA (quick test)
    print("\n4. Cấu hình GA...")
    config = GAConfig(
        population_size=20,
        n_generations=50,
        log_frequency=10
    )
    print(f"   ✓ Population: {config.population_size}")
    print(f"   ✓ Generations: {config.n_generations}")
    
    # Optimize
    print("\n5. Chạy GA Optimizer...")
    print("-" * 70)
    
    optimizer = GAOptimizer(
        teams=teams,
        distances=distances,
        shared_stadiums=shared_stadiums,
        derby_pairs=[(1, 2), (1, 3)],
        config=config
    )
    
    best_schedule = optimizer.optimize()
    
    print("\n" + "=" * 70)
    print("KẾT QUẢ:")
    print(f"Best fitness: {best_schedule.fitness_score:.2f}")
    print(f"Tổng trận: {len(best_schedule.matches)}")
    print(f"Tổng vòng: {best_schedule.get_total_rounds()}")
    print("=" * 70)

if __name__ == "__main__":
    main()