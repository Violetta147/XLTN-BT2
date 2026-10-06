# H17 — nested lựa chọn giữa các phương án đã có

Đăng ký trước tính joint selection, currentfa759d0. Không tạo thuật toán mới hoặc thay estimator/frame/features. Registry cố định7options: acceptedACF, forwardhysteresismargin.02/.04/.06/.08/.12, fixedlogistic2D C1/.5.

Final selection innerLOFO4file, minimumMAPE trongoptions thỏa guards H12 (F1/recallV drop≤.01,SILincrease≤1,maxper-fileMAPEincrease≤2pp,phone_F1std khôngworse nếu có). Tie registryorder, defaultaccepted. Outerheld4fold: chọnoption lại chỉother3 với innerLOFO3, fit onlyother2; retrain selectedoption trênother3 trước heldprediction. Report finalselectedLOFO vànestedprocedure riêng, đồng thời lưuselectionfiles/fitfiles/optionID.

Registry được đề xuất sau khi agent đã xem nhiều train results, nên nested này kiểm soát bước chọn option/parameter hiện tại, không làm biến mất history hoặc chứng minh đánh giá toànbộquátrình khám phá là unbiased. Cảtrain vàtestcũ đều đã từngđượcxem trong lịch sử; chưa mởtestmới vòng này.

GatesPROTOCOLđăngkýgiữ nguyên cho final/nested. Nếunestedfails, khônglấyfixedmodelLOFOđẹpđể thay cho procedure estimate. Khôngchọnfamily bằngouterresult/test. H12gains cómetric-labelcoupling đãđượcghi; bao gồmtradeoffsFP/FNvàUVstatcontributionskhiphântích.
