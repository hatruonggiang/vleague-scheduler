#!/usr/bin/env python3
"""
Script chạy GA optimizer cho V.League scheduling
"""

import sys
import os
from pathlib import Path

# Thêm thư mục gốc vào path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.data_processing.loader import DataLoader
from src.data_processing.validator import DataValidator
from src.data_processing.preprocessor import DataPreprocessor
from src.optimization.config import GAConfig
from src.optimization.ga_optimizer import GAOptimizer
import json
import time

def main():
    """
    Main function
    """
    print("=" * 70)
    print("V.LEAGUE SCHEDULING - GENETIC ALGORITHM OPTIMIZER")
    print("=" * 70)
    
    # 1. Load dữ liệu
    print("\n[1/6] LOAD DỮ LIỆU")
    print("-" * 70)
    
    data_loader = DataLoader(data_dir="data/raw")
    
    try:
        teams = data_loader.load_teams()
        stadiums = data_loader.load_stadiums()
        distances = data_loader.load_distances()
        special_dates = data_loader.load_special_dates()
        
        print(f"✓ Đã load {len(teams)} đội bóng")
        print(f"✓ Đã load {len(stadiums)} sân vận động")
        print(f"✓ Đã load {len(distances)} cặp khoảng cách")
        print(f"✓ Đã load {len(special_dates)} ngày đặc biệt")
        
    except Exception as e:
        print(f"✗ Lỗi khi load dữ liệu: {e}")
        return
    
    # 2. Validate dữ liệu
    print("\n[2/6] VALIDATE DỮ LIỆU")
    print("-" * 70)
    
    validator = DataValidator()
    
    if validator.validate_all(teams, stadiums, distances, special_dates):
        print("✓ Dữ liệu hợp lệ!")
        if validator.get_warnings():
            print("\nCảnh báo:")
            for warning in validator.get_warnings():
                print(f"  ⚠ {warning}")
    else:
        print("✗ Dữ liệu không hợp lệ!")
        validator.print_report()
        return
    
    # 3. Tiền xử lý
    print("\n[3/6] TIỀN XỬ LÝ DỮ LIỆU")
    print("-" * 70)
    
    preprocessor = DataPreprocessor(teams, stadiums)
    preprocessor.print_statistics()
    
    shared_stadiums = preprocessor.get_teams_sharing_stadium()
    
    # 4. Cấu hình GA
    print("\n[4/6] CẤU HÌNH GENETIC ALGORITHM")
    print("-" * 70)
    
    # Có thể chọn config
    print("Chọn loại config:")
    print("1. Quick test (nhanh, ít thế hệ)")
    print("2. Production (chậm, nhiều thế hệ, kết quả tốt)")
    print("3. Custom")
    
    choice = input("Lựa chọn (1/2/3) [default=1]: ").strip()
    
    if choice == "2":
        config = GAConfig.production_config()
        print("✓ Sử dụng production config")
    elif choice == "3":
        pop_size = int(input("Population size [200]: ") or "200")
        n_gen = int(input("Number of generations [1000]: ") or "1000")
        config = GAConfig(population_size=pop_size, n_generations=n_gen)
        print("✓ Sử dụng custom config")
    else:
        config = GAConfig.quick_test_config()
        print("✓ Sử dụng quick test config")
    
    print(config)
    
    # Derby pairs (có thể tùy chỉnh)
    derby_pairs = [
        (1, 2),   # Hà Nội vs Viettel
        (1, 3),   # Hà Nội vs CAHN
        (2, 3),   # Viettel vs CAHN
    ]
    
    # 5. Chạy optimization
    print("\n[5/6] CHẠY OPTIMIZATION")
    print("-" * 70)
    
    optimizer = GAOptimizer(
        teams=teams,
        distances=distances,
        shared_stadiums=shared_stadiums,
        derby_pairs=derby_pairs,
        config=config
    )
    
    start_time = time.time()
    best_schedule = optimizer.optimize()
    end_time = time.time()
    
    print(f"\n✓ Hoàn thành optimization trong {end_time - start_time:.2f}s")
    
    # 6. Lưu kết quả
    print("\n[6/6] LƯU KẾT QUẢ")
    print("-" * 70)
    
    # Tạo thư mục outputs nếu chưa có
    os.makedirs("outputs/schedules", exist_ok=True)
    os.makedirs("outputs/visualizations", exist_ok=True)
    
    # Lưu schedule dạng JSON
    schedule_data = {
        'metadata': {
            'total_rounds': best_schedule.get_total_rounds(),
            'total_matches': len(best_schedule.matches),
            'fitness_score': best_schedule.fitness_score,
            'optimization_time': end_time - start_time
        },
        'matches': []
    }
    
    for match in best_schedule.matches:
        schedule_data['matches'].append({
            'id': match.id,
            'round': match.round_number,
            'home_team_id': match.home_team_id,
            'away_team_id': match.away_team_id,
            'stadium_id': match.stadium_id
        })
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    json_path = f"outputs/schedules/schedule_{timestamp}.json"
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(schedule_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Đã lưu lịch thi đấu: {json_path}")
    
    # Vẽ biểu đồ
    try:
        plot_path = f"outputs/visualizations/fitness_evolution_{timestamp}.png"
        optimizer.plot_history(save_path=plot_path)
        print(f"✓ Đã lưu biểu đồ: {plot_path}")
    except Exception as e:
        print(f"⚠ Không thể vẽ biểu đồ: {e}")
    
    print("\n" + "=" * 70)
    print("HOÀN THÀNH!")
    print("=" * 70)

if __name__ == "__main__":
    main()