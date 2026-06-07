# Updates to code

### 2026-06-06

1. Keep track of flat field std when averaging for exposures. Use the standard deviations in the weights, along with read noise to oust any hot pixels or outliers.
1. Covariance was changed to 'unscaled' in flat field polyfit.
1. Fix an issue where dividing a DataArray by another DataArray would remove attributes with conflicting values.
1. Fix an issue where pos, posh, posl selections were not respected. (step1_fits2ds.py:345 is the root cause)
1. Flat, background, position files need to be background subtracted (done in the previous step). Make sure this happens. [CHECK]
1. L1B calibration was flat-fielding the flat field (and doing a dark subtraction again).
1. 