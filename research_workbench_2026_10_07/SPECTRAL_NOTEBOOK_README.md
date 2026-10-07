# Notebook AMDF phổ và cao độ

`AMDF_SPECTRAL_LOCAL.ipynb` nối kết H42 vàH43 đã đăng ký. NAMDF là AMDF chuẩn hóa biên độ trên phần chồng lấp, dùng độ tương tự khi dịchlag đểtìmchu kỳ; cao độF0=fs/lag. Praat quyết định hữu thanh và làmanchor. Spectralratio làtỷlệ nănglượng phổ≥1kHz của40ms raw, bỏDC/Hann/FFT; không SNR hoặcnhãngiớitính. H42route40ms khi ratio thấp; H43thêmminimumgateF0 từngkhung. Bộđiềukhiển cùngrule cho mọifile, không dùngstatisticsGT lúcinfer.

Nămcodecell tính lại **68rows** từtrainWAV: H24AMDFcontrol4, H42/H43fixed56, nested8. BốnPraatcall mới,8NAMDFcurvegroups25/40ms được tính từPCM và4spectralgroups mới; outputprefix riêng khôngghiđèbenchmark. Notebook dùngreceiptouterchoices đãlưu, không mởgrid/chọnbesttheofile đangchấm. H24control fit3filekhác. Exactcode chạyquaPythonexec/headlessdisplay, không Jupyterkernel; là cáchreplaylocal đãdùngởcácnotebook trước.

Nguồn phảicommit/push trướcreplay. Hiện **source-only/chưa chạy**; chỉ cập nhật đãverified saureceipt vàlayoutcheck. Lệnh: `execute_spectral_notebook.py`, `verify_spectral_notebook.py` bằngPythonlocal. Verifierstatsstd(ddof0)/count/MAPE/VUV/LAB/PCM/source/nativebinary/calls/fitexclusions/choices/curves/spectralparity/PNGSVG/status. Benchmarkverifier trướcđó kiểmtraphép tínhđộc lập fullFFT/PCM/kernel; notebookverifier thêmfreshoutputparity.

Kết quả cần giữ rõ: H43fixed170Hz cùngcấuhìnhtrên4fileAverage≤2% nhưngnestedstudio_M1 chọn140Hz rồiAvg2.523880%; H43tấtcả8gatecontrolPASS chưađủtargettừngfile. H42nestedtargetFAIL. H41nestedtarget đạt nhưngphone_F1stdgateFAIL. Không đánhđồngfixed/nested/mean/centsaccuracy hoặc đổiGT. Bốntrain đãxemnhiềuvòng, chưaindependentnewcorpusvalidation. Khôngpromote/frozen/original/notebooks cũ/testinference/tuning/Drive/PDF/deeplearning/MCP retry.
