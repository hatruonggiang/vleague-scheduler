Giải thích các thư mục chính
1. data/**
- Chứa tất cả dữ liệu đầu vào
- Tách biệt 'raw' (dữ liệu gốc) và 'processed' (dữ liệu đã được xử lý)
- 'constraints/' chưa định nghĩa ràng buộc với trọng số
2. 'src/'
- 'models/': định nghĩa các class cơ bản (Team, Stadium, Match, Schedule)
- 'ga/': Toàn bộ logic GA (encoding, operators, fitness)
- 'constraints/': Kiểm tra và đánh giá ràng buộc
- 'optimization/': Main optimizer và post-processing

3. 'outputs/'
- Lưu tất cả kết quả: Lịch, log, visualization, reports
- Mỗi lần chạy tạo file riêng với timestamp

4. 'tests/'
- Unit tests cho các module quan trọng
- Đảm bảo code chạy đúng

5. 'notebooks/'
- Dùng để thử nghiệm, phân tích
- Tune parameters của GA

6. 'configs/'
- Tách riêng configuration ra file YAML
- Dễ thay đổi parameters mà không sửa code

7. 'scripst/'
- Các script tiện ích chạy nhanh
- Entry points cho các tác vụ phổ biến

Workflow sử dụng
1. Chuẩn bị dữ liệu -> data/raw/
2. Chạy preporcessing ->data/processed/
3. Chạy GA optimizer ->outputs/schedules/
4. Đánh giá kết quả -> outputs/reports/
5. Visualize -> outputs/visualizations/

Dependencies chính (requirements.txt)
deap>=1.4.0
numpy>=1.24.0
pandas>=2.0.0
pyyaml>=6.0
openpyxl>=3.1.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.14.0
jupyter>=1.0.0
pytest>=7.3.0