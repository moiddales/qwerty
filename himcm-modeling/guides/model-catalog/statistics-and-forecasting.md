# Statistics, data processing and forecasting

Use these to **understand relationships, clean and fill data, and forecast** over time: CO2 and temperature (2022B), lake levels (2021B), HPC energy and emissions (2024B), thermostat learning (2018B), roller-coaster data (2018A).

## Data processing

| Method | Corpus examples | Watch for |
|---|---|---|
| Correlation matrix / heatmap to find redundant variables | [2018A-8744](../../papers/2018A-8744.md), [2018A-8700](../../papers/2018A-8700.md), [2021B-11576](../../papers/2021B-11576.md) | Correlation is not a reason to drop a variable that matters for a different reason |
| Regression imputation (including iterative chains) | [2018A-8992](../../papers/2018A-8992.md), 2018A-8744 | Report R²; avoid predicting from already-imputed values without saying so |
| Nearest-neighbor or within-cluster donor imputation | [2018A-8554](../../papers/2018A-8554.md) | Justify the distance and the clusters |
| EM algorithm, neural-network imputation | [2018A-8874](../../papers/2018A-8874.md), 2018A-8700 | Harder to explain; show the check |
| Physics-based filling | 2018A-8874 (v = √(2gh), centripetal force) | Check assumptions behind the formula |
| Outlier detection (z-score, IQR) | 2018A-8700, [2021B-11823](../../papers/2021B-11823.md) | Check extremes against sources before deleting |
| Box-Cox or log transformation | 2018A-8744, [2020A-11135](../../papers/2020A-11135.md) | Show before/after distributions |
| PCA | 2018A-8700 (dimension check) | Components need interpretation |
| Clustering (k-means, hierarchical) | [2020A-10549](../../papers/2020A-10549.md), [2020A-10701](../../papers/2020A-10701.md), 2018A-8554 | Justify k (elbow, dendrogram) |

## Relationships and trend testing

- **Linear and multiple regression** to quantify drivers (2021B-11898 regressed monthly elevation on temperature, precipitation and wind) or to fit geometry tables (volume against elevation in 2021B-11552 and 2021B-11576). With few points (2021B-11898 used 12 monthly values), treat the result as indicative.
- **Logarithmic and other functional forms** chosen from theory: log(CO2) as the temperature driver, justified by physics (2022B-12465, pp. 4–5); energy against computing power (2024B-15022).
- **Trend tests**: the Mann-Kendall test, including a modified version for autocorrelated data (2022B-12465; 2021B-12384). Make sure the test answers the question asked. A test that shows a monotone rise does not show that the most recent rise is faster than earlier ones (see the note in 2022B-12465).

## Forecasting

| Method | Corpus examples | Watch for |
|---|---|---|
| Regression on time (linear, quadratic, exponential) | [2022B-12465](../../papers/2022B-12465.md), [2024B-15022](../../papers/2024B-15022.md) | Different forms agree in-sample and diverge far out; compare them on hold-out data |
| Weighted moving average, adaptive filtering | [2021B-11898](../../papers/2021B-11898.md), [2018B-8506](../../papers/2018B-8506.md) | Short windows carried far forward |
| Exponential smoothing (Holt) | 2022B-12465 | Choose seasonal or non-seasonal on evidence |
| ARMA / ARIMA, with stationarity test and order selection | [2021B-11552](../../papers/2021B-11552.md), 2021B-11576, 2021B-11823, [2024B-15502](../../papers/2024B-15502.md) | Needs enough data; four annual points are not enough |
| Trend + seasonal + residual decomposition (STL, seasonal means) | 2021B-11576, 2022B-12465 | Restore seasonality in long forecasts |
| Regression with a sinusoidal seasonal term | 2021B-11898, [2021B-12384](../../papers/2021B-12384.md) | State the period and fit |
| Grey model GM(1,1) | 2024B-15502 | Designed for very short series; extrapolations grow quickly |
| Regression with ARIMA errors | 2022B-12465 (log-CO2 with ARIMA(6,1,0) errors) | Explain both parts |
| Bootstrap for forecast uncertainty | 2022B-12465 (moving block bootstrap) | Report the interval, not only the mean |
| Period detection by autocorrelation | 2018B-8506 (each user's routine, p. 7) | Needs enough cycles of data |

**Validation for forecasts.** Hold out the most recent data and forecast it (2022B-12465 used forward-chaining cross-validation and train/test scenarios; 2021B-11823 back-tested 1935–2010 against 2011–2021). Report an error measure (RMSE, MAE, MAPE). Compare far-future values with physical or logical limits (2021B-11898 compared 2050 levels with dead pool).

**The training window decides the forecast.** In 2021B, papers that fitted on months of data and those that fitted on decades reached very different 2050 values. Tie the window to your definitions, say why you chose it, and show what a different window gives.

## Outside the corpus

Not seen in the carded papers, but often suitable:

- **Prediction intervals from the model itself** (regression or ARIMA standard errors) on every forecast plot.
- **Logistic (S-curve) or Bass diffusion models** for adoption that saturates (technology uptake, market share). A pure exponential cannot saturate.
- **Piecewise (segmented) regression** to detect a change in trend, for example "is the recent rise faster?".
- **Quantile regression** when the question is about extremes rather than averages.
- **Simple ensembles**: average several reasonable models and use their spread as a rough uncertainty band.
- **Leave-one-out or k-fold cross-validation** for small non-time-series data sets.
