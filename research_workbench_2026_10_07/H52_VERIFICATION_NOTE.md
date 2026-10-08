# Kiểm tra H52

Bộ kiểm v1 thất bại ở phone_F1/default, một khung98: independent231/228Hz khác raw. Nguyên nhân là thứ tự phép tính float trong independent DP: a+b−c thay vì a+(b−c), và w×difference/mean thay vì w×(difference/mean), có thể đổi hướng khi chi phí gần hòa. v2 giữ thứ tự số học của công thức vendor, vẫn scalar independent loops và last-index tie. Không nới tolerance, không sửa source đăng ký hoặc đo lại output. V1/failure JSON giữ nguyên.

v2 PASS train:5148native path frames,5148PCM fullFFT NLFER frames,24metric groups,16proofs; default raw/canonical parity H40_f35 PASS. Giới hạn: không independently reimplement toàn bộ spectral/candidate generation. Canonical lệnh: verify_yaapt_extension_v2.py train/test.

Final và4outer selections đềuhard170; nested perfile0.34008/0.77615/1.47358/1.90992%, không cải thiện. Frozen test options control hard170 vàYAAPTdefault được đăng ký trước; default chỉ diagnostic, không được chọn theo test.
