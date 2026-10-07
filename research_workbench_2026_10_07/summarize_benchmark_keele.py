import json
from pathlib import Path

import numpy as np
import pandas as pd
import benchmark_keele as benchmark

HERE=Path(__file__).resolve().parent


def main():
    result=json.loads((HERE/'results/H49_experiment.json').read_text())
    verification=json.loads((HERE/'results/H49_verification.json').read_text())
    assert verification['experiment_sha256']==benchmark.audit.digest(HERE/'results/H49_experiment.json')
    data=pd.read_csv(HERE/'results/H49_metrics.csv')
    candidate=data.query("model == 'candidate'")
    summary=pd.DataFrame([dict(model=k,**v) for k,v in result['summaries'].items()])
    chosen=result['summaries']['candidate']; control=result['summaries']['control']
    manifest=json.loads((HERE/'results/H49_dataset_manifest.json').read_text())
    duration=sum(case['duration_s'] for case in manifest['cases'])
    weighted_mae=float(np.average(candidate.mae_hz_both_voiced,weights=candidate.TP))
    voice_recall=candidate.TP.sum()/candidate.voiced_reference_frames.sum()
    mean_delta=chosen['file_mean_average_mape']-control['file_mean_average_mape']
    rpa_delta=chosen['rpa50_pct']-control['rpa50_pct']
    table=candidate[['file','gpe20_pct','vde_pct','rpa50_pct','F0mean_mape','F0std_mape','F0num_mape','average_mape']].copy()
    table.columns=['File','GPE20 (%)','VDE (%)','RPA50 (%)','MAPE mean (%)','MAPE std (%)','MAPE count (%)','Average MAPE (%)']
    text=[
        '# Kiểm tra pipeline BT2 trên KEELE', '',
        f'Đã chạy cấu hình cố định trên tất cả 10 bản thu KEELE: 5 nam, 5 nữ, tổng {duration:.2f} giây. Không học hoặc chọn tham số từ KEELE. Kết quả không đạt tiêu chí chẩn đoán đã đăng ký, và không file nào đạt Average MAPE <2%. Vì vậy phép thử này chưa hỗ trợ kết luận rằng kỹ thuật đã tốt và lỗi BT2 chỉ do thiếu dữ liệu.', '',
        'Pipeline đang được kiểm tra là Praat 7.0.02 filtered autocorrelation với ngưỡng hữu thanh 0,30, sau đó NAMDF hard170 tinh chỉnh F0. Đây là cấu hình chọn từ các thí nghiệm BT2; không phải notebook ACF đã nộp. Control dùng cùng đầu ra Praat trước bước NAMDF. Giữ khoảng F0 70–400 Hz, cửa sổ NAMDF 25/40 ms, bước dịch 10 ms và tần số lấy mẫu KEELE 20 kHz.', '',
        '## Kết quả tổng hợp', '',
        benchmark.audit.markdown_table(summary[['model','gpe20_pct','vde_pct','ffe20_pct','rpa50_pct','file_mean_average_mape','worst_file_average_mape','files_average_mape_lt2']]), '',
        'GPE20 là tỷ lệ sai cao độ hơn 20% trong các khung mà cả tham chiếu và thuật toán đều nhận hữu thanh. Chỉ số này không tính khung hữu thanh bị bỏ sót. VDE đo sai quyết định hữu thanh trên toàn bộ khung chấm. FFE20 tính cả sai quyết định hữu thanh và sai cao độ lớn. RPA50 đo tỷ lệ khung tham chiếu hữu thanh được dự đoán đúng F0 trong 50 cents, khoảng 3% về tần số; bỏ sót được tính là sai. GPE/VDE/FFE thấp hơn tốt hơn; RPA cao hơn tốt hơn.', '',
        f'Trên {chosen["frames"]:,} khung được chấm, pipeline có GPE20 {chosen["gpe20_pct"]:.4f}%, VDE {chosen["vde_pct"]:.4f}%, FFE20 {chosen["ffe20_pct"]:.4f}% và RPA50 {chosen["rpa50_pct"]:.4f}%. MAE F0 trên các khung cùng hữu thanh là {weighted_mae:.4f} Hz; recall hữu thanh {100*voice_recall:.4f}%. Có {int(candidate.FN.sum())} khung hữu thanh bị bỏ sót và {int(candidate.FP.sum())} khung không hữu thanh bị nhận nhầm.', '',
        f'Bước NAMDF làm RPA50 thay đổi {rpa_delta:+.4f} điểm phần trăm so với Praat; Average MAPE trung bình từng file thay đổi {mean_delta:+.4f} điểm phần trăm. Một chỉ số thống kê cải thiện nhẹ trong khi độ chính xác từng khung giảm: chưa có bằng chứng bước tinh chỉnh này tốt hơn Praat trên corpus mới.', '',
        '## Từng bản thu', '', benchmark.audit.markdown_table(table), '',
        'Mean/std/count tham chiếu trong bảng được tính từ đường F0 KEELE trên cùng các thời điểm được chấm. Chúng không có cùng quy trình tạo chuẩn với ba thống kê thầy cung cấp cho BT2. Average MAPE dưới 2% vẫn được báo riêng, nhưng không thay cho việc chấm F0 từng khung.', '',
        '## Điều phép thử cho thấy và chưa cho thấy', '',
        'Pipeline ít mắc lỗi cao độ lớn trong các khung đã nhận hữu thanh, nhưng còn bỏ sót hoặc lệch F0 nhỏ ở khá nhiều khung. Vì thế chỉ nhìn GPE20 khoảng 0,8% sẽ quá lạc quan. Tiêu chí chẩn đoán đăng ký trước là RPA50 ≥90%, VDE ≤10% và FFE20 ≤10%; RPA50 không đạt. Các mốc này là tiêu chí của phép thử, không phải chuẩn chính thức của KEELE.', '',
        f'Có {int(candidate.reference_voiced_outside_70_400.sum())} khung tham chiếu hữu thanh nằm ngoài khoảng 70–400 Hz. Giới hạn khoảng F0 là một yếu tố kỹ thuật có thể ảnh hưởng kết quả; các khung này được giữ trong mẫu số để không che lỗi. Đồng thời có {int(candidate.unknown_reference_frames.sum())} khung tham chiếu âm được loại vì không có tham chiếu đáng tin cậy. Coverage theo thời gian đạt trên 99,8% từng file. Không dịch đường tham chiếu để tìm kết quả tốt nhất.', '',
        'KEELE có đường pitch kiểm tra bằng tay từ tín hiệu laryngograph, nhưng tài liệu gốc cảnh báo không coi nó là ground truth khớp chính xác khi cửa sổ phân tích khác. Tham chiếu dùng ACF khoảng 25,6 ms, trong khi gate Praat và NAMDF của ta có cửa sổ khác; độ trễ laryngograph–microphone cũng chỉ được hiệu chỉnh một phần. Do đó đây là kiểm tra chẩn đoán, không chứng nhận tuyệt đối độ chính xác F0. Không có nhãn SIL riêng trong KEELE này, nên không báo số khung false_voiced_sil như thể đã đo được; tham chiếu zero chỉ cung cấp lớp không hữu thanh.', '',
        'Một benchmark tốt cũng chỉ chứng minh pipeline hoạt động trên corpus đó. Nó không loại trừ lỗi kỹ thuật riêng cho tiếng Việt, khác điều kiện thu, khác khoảng F0 hoặc khác cách tạo nhãn thống kê BT2. Kết quả hiện tại càng không đủ để quy nguyên nhân riêng cho thiếu data. Với cấu hình hard170 không học hệ số, dữ liệu ít chủ yếu hạn chế việc chọn và kiểm chứng tham số; tăng số bản sao không tự giải quyết vấn đề này.', '',
        '## Kiểm tra và tái lập', '',
        f'Preregistration source/registry/manifest đã push và xác minh trước phép đo ở commit a2eec84. Verifier đã tính lại {verification["independent_curve_rows"]:,} đường NAMDF của 20 nhóm cửa sổ, kiểm full FFT, chọn ứng viên độc lập, căn thời gian, 20 nhóm metric và hash nguồn/dữ liệu. Không gọi lại Praat trong verifier. Mười call Praat trong phép đo và thời gian {result["wall_time_s"]:.2f} giây không phải benchmark latency của thuật toán vì còn gồm lưu bằng chứng.', '',
        'Lệnh: `python research_workbench_2026_10_07/benchmark_keele.py acquire`, `check`, `register`, `run`, rồi `python research_workbench_2026_10_07/verify_benchmark_keele.py`. Các output đã hoàn tất được bảo vệ khỏi ghi đè; không chạy lại register/run trên cùng thư mục nếu chưa tạo phiên riêng. Dữ liệu download ở benchmark_data được gitignore, chỉ manifest/checksum và bằng chứng đo được commit. WAV/LAB BT2, notebook đã nộp và frozen config gốc giữ nguyên.', '',
        'Nguồn corpus: [Bechtold, Zenodo3921794](https://zenodo.org/records/3921794); README gốc trích trong sources/H49_KEELE_README.txt; [conversion code đã ghim commit](https://github.com/bastibe/Replication-Dataset-Scripts/blob/a29546dba8824c4bbba7573c7d795304830d0045/keele.py). Tham khảo cách đọc GPE và lỗi hữu thanh ở [trang tác giả](https://bastibe.github.io/Dissertation-Website/replication-dataset/index.html). Workflow tra cứu dùng literature-review local từ [Scientific Agent Skills](https://doi.org/10.48550/arXiv.2609.00065); không dùng skill prose. Chi tiết query và giới hạn nội dung đã đọc trong BENCHMARK_SOURCES.md.', '',
        'Cách chia validation và áp dụng protocol: PROTOCOL_F0.md. Bốn protocol intra/cross-type của chống giả mạo khuôn mặt không phải bốn phép thử bắt buộc của bài F0.'
    ]
    (HERE/'BENCHMARK_KEELE_REPORT.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    benchmark.audit.json_write(HERE/'results/H49_reporting_verification.json',dict(
        metrics_sha256=benchmark.audit.digest(HERE/'results/H49_metrics.csv'),
        experiment_sha256=benchmark.audit.digest(HERE/'results/H49_experiment.json'),
        benchmark_verification_sha256=benchmark.audit.digest(HERE/'results/H49_verification.json'),
        report_sha256=benchmark.audit.digest(HERE/'BENCHMARK_KEELE_REPORT.md'),
        generator_sha256=benchmark.audit.digest(__file__),weighted_mae_hz_both_voiced=weighted_mae,
        pooled_voiced_recall=float(voice_recall),no_new_measurements=True))
    print('Saved readable report from verified measurements')


if __name__=='__main__':
    main()
