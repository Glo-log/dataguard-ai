# Streamlit Community Cloud preparation

This repository is prepared for deployment; it has **not been published** and there is no public deployment URL.

1. Review the repository, tests, attribution, and screenshots. Follow `docs/GITHUB.md` to publish only after you choose to do so.
2. In your Streamlit Community Cloud workspace, create an app from that repository and branch `main`.
3. Set the entry point to **`app/main.py`**. Select **Python 3.12** in the advanced settings. Root `requirements.txt` supplies the locked dependencies and root `.streamlit/config.toml` supplies the theme and upload limit.
4. No credentials, secrets, database setup, or startup downloads are required. The application loads committed public samples using paths derived from `__file__`.
5. Deploy, then verify the actual public URL: open every page, switch datasets, run the wine model, preview/apply/restore cleaning, run SQL examples, and download exports. Review cloud logs and resource usage before sharing the URL.

Follow the official [Community Cloud deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app) for current account and deployment UI details.

Local testing uses Windows/Python 3.12. A Linux CI workflow is included; remote GitHub Actions and actual cloud dependency resolution remain unverified until they run. The sample workload is deliberately small; no production capacity claim or concurrent-user load test is provided. Full retail Excel conversion is an offline CLI task, not a cloud startup task.

Uploads are processed on the hosting server, kept in temporary session memory, and excluded from shared data caches. This is not a private or authenticated data portal. Use public or non-sensitive files for a public demo. Session data is not a durable audit trail; reconnects or restarts may discard it. Users should download results. Do not commit upload files, secrets, local reports, raw data, environments, or databases.
