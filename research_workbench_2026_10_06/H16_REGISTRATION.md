# H16 — logistic V/UV trên hai đặc trưng đã có

Đăng ký trước đo. Champion009fd2c, source8f99791; H12provisional. Chỉ thay mô hình quyết định V/UV, giữ hai inputs có sẵn ACFscore/relativeRMS, RMSgate cuối, candidates/path/median3/frame25/hop10. Không thêm ZCR/spectralfeatures hoặc tune threshold trong H16.

Logistic L2 C=1, thresholdscore.5, max_iter500. StandardScaler fit trainingonly; per-file/per-class sampleweights cân bằng4files và V/UV, không fit SIL vào logistic. Energygate vẫn fitV/SIL đúng core trên cùng trainfold. Classscore không phải probability calibrated trên deployment.

Hypothesis: đường biên tuyến tính hai chiều có thể giảm một phần lỗi khi scoreACF và energy kết hợp, thay vì chỉACFthreshold + hardRMS. Báo cả FP/FN/SIL, file-stat3GT và metric-labelcoupling; không coi MAPE giảm từUVestimate là repairpitch.

No newparameter selection, train vàLOFOheld-file, không fake nestedscore. GatesPROTOCOL và criticalphone_F1std giữ nguyên. Testchưađọc. Assertions: fit IDs loạiheld; scaler/model finite vàconverged; manualsigmoid khớpsklearn; GTpoison khôngđổi inference; coefficient/scaler metadata lưuJSON đểtái lập.
