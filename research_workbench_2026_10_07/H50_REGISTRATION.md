# H50 — khôi phục hữu thanh bằng học có/không giám sát

Đăng ký trước đo. Điểm quay lại `d148a2e0deb60442218002431f6494a16fad7e30`; baseline toán học gốc H31/frozen giữ nguyên. Control trực tiếp là H43 hard170 đã xác minh H47/H48. Vòng này là bước cơ chế trước ma trận mở rộng người dùng vừa yêu cầu, không được gọi là thử hết.

Giả thuyết: H47 chỉ loại thêm khung. H50 học trên mọi khung train và chỉ thêm các khung baseline bỏ sót; có thể tăng recall nhưng làm count/std MAPE xấu đi. Không sửa LAB hoặc F0num để đạt điểm. Nhãn chuẩn lấy tại tâm khung từ LAB. So nhãn tâm với phần lớn cửa sổ chỉ là chẩn đoán, không thay nhãn chấm hoặc chọn quy tắc theo score.

Năm options: hard170, logistic base4, logistic base4+13MFCC, GMM base4, GMM base4+13MFCC. Base4: max normalized ACF 70–400Hz, log relative RMS q95 sau trừ mean, ZCR crossings/s, Hann spectral energy >=1000Hz ratio. FFT next power of two, DC bỏ, trọng số một phía đúng. MFCC tự triển khai: 26 triangular HTK mel bands 70–min(8000,Nyquist)Hz, normalized spectral power, log floor1e-12, DCT-II orthonormal, coefficients1–13; bỏ c0, không preemphasis/resample. Đây là đặc trưng phổ cho quyết định V/UV, không phải 13 giá trị F0.

Chia khung raw25ms/hop10ms và chấm cùng grid baseline. Pitch cũ giữ nguyên ở mọi khung đã hữu thanh. Pitch khôi phục lấy peak local normalized ACF đầu tiên đạt .93 lần strength peak lớn nhất, parabolic refinement delta clamp±.5, range70–400Hz. Đặc trưng maxACF vẫn là maximum strength. Cùng mọi learner: chỉ khôi phục khi probability >=.5, maxACF >=.6, relative RMS >=.01, pitch hữu hạn. Không smoothing hoặc đổi pitch cũ. Do thay đổi chính là nhánh recovery, không tuyên bố đã cô lập chất lượng ACF pitch mới với bộ phân loại.

Lỗi trước measurement: prototype chọn strongest peak không vượt probe tone200Hz (có thể chọn100Hz do peaks bội gần bằng nhau). Đã sửa earliest peak>=.93max trước registry/commit/push và trước đọc PCM BT2 cho H50. Không nới tolerance để gọi probe PASS.

Mỗi fit pool lấy cùng số khung mỗi file bằng round(linspace(0,N-1,minN)); không lấy mẫu theo nhãn. StandardScaler chỉ fit pool. Logistic C1/natural prior/maxiter1000, V vs UV/SIL. GMM3 diagonal, reg1e-3, n_init5, seed50, tol1e-4/maxiter500; không đọc nhãn để fit hoặc gán nghĩa cụm. Cụm có mean periodicity cao nhất là V; hai cụm còn lại gộp non-V, không khẳng định chúng đúng là UV/SIL. Đây là unsupervised fit + quy tắc vật lý cho nghĩa cụm; lựa chọn pipeline bằng validation có nhãn vẫn có giám sát.

Nested leave-one-file-out: bốn outer folds, ba inner held files cho mỗi outer; final inner LOFO bốn train. Minimax worst Average MAPE, rồi mean/ID. Invalid nếu F1/recallV giảm>.01 hoặc SIL tăng>1 so hard170 cùng pool. Giữ tám gates cải thiện của H47, nhưng so trực tiếp hard170; target strict từng nested file<2 riêng. Các kết quả vẫn exploratory do bốn train đã xem nhiều vòng; test và KEELE đã xem lịch sử, không dùng trong H50.

Lưu mọi fixed LOFO, inner traces, fit coefficients/GMM params, khung recovered V/UV/SIL, center/majority overlap, môi trường, input/output/source hash. Kiểm synthetic tone/silence/gain/DC trước commit/push/remoteverify rồi mới đo. Verifier độc lập tính lại PCM features, DCT và FFT full, direct ACF peak, mô hình/fold/selection, MAPE/VUV/SIL và bất biến giữ pitch cũ. Không native calls mới. Không Drive/DL/Jev/prose skill/PDF.

Nguồn API đã đọc HTML 07/10/2026: [GaussianMixture](https://scikit-learn.org/stable/modules/generated/sklearn.mixture.GaussianMixture.html), [MathWorks pitch/MFCC](https://www.mathworks.com/help/audio/ug/speaker-identification-using-pitch-and-mfcc.html). Librosa MFCC HTML trả Internal Error; không dùng nội dung lỗi hoặc PDF. MFCC trên đây là cấu hình của thí nghiệm, không tuyên bố khớp default của MATLAB/librosa. H22/H47 và H34/H35 là bằng chứng local ZCR/ML/SWIPE đã thử, không chạy lại.

Lệnh local: `C:/Users/violet/miniconda3/python.exe research_workbench_2026_10_07/voicing_recovery.py check`, `run`; rồi `verify_voicing_recovery.py`.
