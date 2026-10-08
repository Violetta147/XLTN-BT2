function pefac_bridge(input_path, output_path)
  pkg load image;
  here = fileparts(mfilename('fullpath'));
  addpath(fullfile(here, 'vendor', 'voicebox_pefac'));
  data = load(input_path);
  [fx, tx, pv, fv] = v_fxpefac(data.audio(:), data.fs, 0.01, '', struct('flim', [70 400]));
  runtime = version;
  image_filter = which('imfilter');
  image_pad = which('padarray');
  source = which('v_fxpefac');
  save('-mat7-binary', output_path, 'fx', 'tx', 'pv', 'fv', 'runtime', 'image_filter', 'image_pad', 'source');
end
