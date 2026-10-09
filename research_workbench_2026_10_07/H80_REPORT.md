# H80 — nhận ra thay đổi trong dòng âm thanh ghép nối

Ngày09/10/2026. Prereg c21c823923983f3b60719815797331d96f8f3ade đã push và xác minh remote trước đo; rollback5bef022eca128f2d6531b5c68c492353c82eb28b. Câu hỏi của người dùng là ghép nối các file rồi để mô hình tự tìm nhóm/đoạn. Hypothesis FAIL, verifier PASS. Không đo F0 hoặc test mới; kết quả này không thay Average MAPE của BT2.

Đã ghép physical samples bản sao bốntrain về cùng16kHz: phone_F1/studio_F1/phone_M1/studio_M1, rồi đảo thứtự. Không chèn silence/crossfade/resetframes tại join, không dùng fs khác nhau hoặc vị trí file để model biết đoạn nào. Resampling SciPy1.17.1 Kaiser5/zeroextension, source khóa. Analysisframes thật25ms400samples/hop10ms160samples,nopadding; context blocks25frames, step250ms, không đổi analysiswindow thành250ms. Có52blocks mỗi stream.

Reuse dictionary4component H79fulltrain, không chọn noisecomponent hoặc lọc audio trongH80. NNLSfixedbasis cho2streams, coefficient≥0; features q20logRMS,medianhighfreqratio,bốnmeancomponentshares. StandardScaler/KMeans2/10starts/seed80fit một lần primary,3iterations; reverse dùng nguyênscaler/centers. Clusters0/1 chưa có tênphone/studio. Emission squaredEuclidean/2, dynamicprogram fixedswitchpenalty3; toànstreamoffline. Manifest/domain/sex chỉ dùng chấm saupredict. Không NN neural/attention/consciousness, không gọi unsupervisedclusters là nguồnsemantic đã biết.

primary/raw: domainARI 0.075769, sexARI 0.008241, fileARI 0.040406, domainaccuracyup-to-permutation 0.653846; predictedboundaries 8, matched 2/3, precision 0.250000, recall 0.666667, meanmatchedabserror 0.080000s (tolerance0,35s).

primary/decoded: domainARI 0.100870, sexARI -0.000380, fileARI 0.051139, domainaccuracyup-to-permutation 0.673077; predictedboundaries 4, matched 1/3, precision 0.250000, recall 0.333333, meanmatchedabserror 0.005750s (tolerance0,35s).

reverse/raw: domainARI 0.053291, sexARI -0.002830, fileARI 0.021224, domainaccuracyup-to-permutation 0.634615; predictedboundaries 10, matched 2/3, precision 0.200000, recall 0.666667, meanmatchedabserror 0.068375s (tolerance0,35s).

reverse/decoded: domainARI 0.052514, sexARI -0.012379, fileARI 0.026267, domainaccuracyup-to-permutation 0.634615; predictedboundaries 4, matched 1/3, precision 0.250000, recall 0.333333, meanmatchedabserror 0.132687s (tolerance0,35s).

ARI là chỉ số so cách chia nhóm có điều chỉnh mức trùng hợp ngẫu nhiên:1tương ứngpartitiontrùngnhau,0gầnchance-adjustedalignment. DecodedARI chỉ0,100870/0,052514,thấp hơn0,5đãđăngký. Accuracy67,31%/63,46% làbestlabelpermutation trên cùngstreamtrain, không phải accuracy của router đãkhóa semanticmapping trênunseenfiles. SexARI cũng gần0, không đủ kết luận cáccluster đang tách giới tính. Raw tìm đúng2/3join nhưng có8/10điểmđổi, precision25%/20%. Fixedsmoothing giảmfalsechangesxuống4song chỉ giữ1/3join; không sửa penalty sauxemresults. Mốcđổi thậtđược dùng tối đa1-to-1/tolerance0,35s/maxcardinality rồiminsumerror.

Đổi thứtự làm block alignment khác; reverse cùngbốnnguồnaudio không phải externaltest hoặcunseen-file generalization. Việc dùng dictionary họcchung bốnfile không biến 52blocks thành52môi trường độc lập. Kết quả FAIL không chứng minh không tồn tại pattern chung; nó bác bỏ cách biểu diễn/phân nhóm/tách nhãn cụ thể ở đây đủ nhận ra môi trường theo tiêu chí.

Verifier độc lập PASSphysicalFIRresampling/concatidentity/FFT/NNLSKKT/context/scaler/centroidassignmentSSE/temporalglobalcost/ARIcontingency/boundarymatching/hashes. MaximumNNLSprojectedgradient6,308430340606908e-16; khôngrefitcluster hoặcoptimizer. PNGstream_groups.png đãrender/xem: đườngxanh làphone/studiotheomanifest chỉđểchấm, đườngcam làcluster0/1sau giải mã đặt lêncao cho dễnhìn, numericindex chưasemanticmapping. Cácđườnggray làjointhật.

H80hypothesisFAIL, khôngpromote hoặc dùng cluster làm routerF0. H79NMFnoiseproxy cũng chưa đạttrain vàguard; H78guidedsoftgate nhận đúngfulltrain nhưng chỉ2/4domainheld vàheldselectiongiữcontrol. Bestretainedpipeline vẫnH71/H72energy07: meantrain1,305508%, meantest2,196094%,7/8file; phone_M2test4,422661%. Các phép thử kết hợpfile/phânrã này chưa giải quyết mục tiêu mỗifile<2%. Không rerun H00–H80/R01/R02; khôngtesttune/notebookedit/originalGTchanges.

Nguồnprimary [KMeans1.8.0](https://scikit-learn.org/1.8/modules/generated/sklearn.cluster.KMeans.html), [NMF1.8.0](https://scikit-learn.org/1.8/modules/generated/sklearn.decomposition.NMF.html), [resample_poly](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.resample_poly.html). HTMLSciPydoc1.18.0, runtime1.17.1source đọc/khóa khôngupgrade. Kassis,T., Agarwal,V., He,Y., Patel,D., Brueckner,A.M.(2026), [ScientificAgentSkills](https://arxiv.org/abs/2609.00065), DOI10.48550/arXiv.2609.00065 đãbổsungnhưyêucầutrướccủangườidùng. KhôngDrive/DL/PDF/Jev/GPU/Colab/schedule/merge main.
