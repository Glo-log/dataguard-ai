# Dataset license and attribution

The CSV files in `data/sample/` are real subsets adapted from these UCI datasets:

- Chen, D. (2015). **Online Retail** [Dataset]. UCI Machine Learning Repository. DOI: [10.24432/C5BW33](https://doi.org/10.24432/C5BW33). [Source](https://archive.ics.uci.edu/dataset/352/online+retail). Applies to `online_retail_sample.csv`.
- Cortez, P., Cerdeira, A., Almeida, F., Matos, T., & Reis, J. (2009). **Wine Quality** [Dataset]. UCI Machine Learning Repository. DOI: [10.24432/C56S3T](https://doi.org/10.24432/C56S3T). [Source](https://archive.ics.uci.edu/dataset/186/wine+quality). Applies to `wine_red_sample.csv` and `wine_white_sample.csv`.

Both UCI source pages state **Creative Commons Attribution 4.0 International (CC BY 4.0)**. [License summary](https://creativecommons.org/licenses/by/4.0/) · [Full legal terms](https://creativecommons.org/licenses/by/4.0/legalcode).

Changes by DataGuard AI contributors: Excel to UTF-8 CSV and ISO timestamps for retail; semicolon to comma CSV and normalized column names for wine; deterministic selection of source rows for both. No values were fabricated, imputed, deduplicated, or automatically corrected. Complete transformations, selected original row positions, and output hashes are in `sample/provenance.json`. Original archives and complete converted files can be reproduced by the scripts but are excluded from Git.

Preserve this attribution, source and license links, and a description of your changes when redistributing derivatives. The original creators and UCI do not endorse this application. Project code is licensed separately under MIT.

The source data depicted in application screenshots and summarized in measured reports is derived from these same datasets; retain this attribution with redistributed data-bearing illustrations and reports as well.
