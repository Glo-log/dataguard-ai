# DataGuard AI

**A simple way to check, clean, and understand your data before using it.**

DataGuard AI is a Python-based data analysis application I built to make data quality checks easier and more practical.

Real-world datasets are rarely perfect. They often contain missing values, duplicates, inconsistent entries, and unusual observations. DataGuard AI brings the tools needed to explore these problems into one interactive dashboard.

The goal is simple: **help users understand their data, identify potential issues, and make better decisions before analysis.**

## Features

- **Data Overview:** Get a quick summary of your dataset, including its size, columns, and data types.
- **Data Quality Checks:** Find missing values, duplicate records, and values that don't follow defined rules.
- **Exploratory Data Analysis:** Explore distributions, correlations, and trends through interactive charts.
- **Anomaly Detection:** Use Isolation Forest to identify unusual numerical observations worth investigating.
- **Data Cleaning:** Preview and apply cleaning operations while keeping the original data available.
- **SQL Analytics:** Run SQL queries to explore and summarize data.
- **Export Results:** Download cleaned datasets, quality reports, anomaly results, and transformation history.

The application includes eight Streamlit pages covering these features.

## Application Preview

Here are a few screenshots of DataGuard AI in action.

### Dashboard Overview

![Dashboard Overview](assets/screenshots/overview.png)

### Data Quality Report

![Data Quality Report](assets/screenshots/retail_quality.png)

### Anomaly Detection

![Anomaly Detection](assets/screenshots/wine_anomalies.png)

## Technologies Used

| Technology     | Purpose                                  |
| -------------- | ---------------------------------------- |
| Python         | Main programming language                |
| Streamlit      | Interactive web application              |
| Pandas & NumPy | Data processing and analysis             |
| Plotly         | Interactive data visualization           |
| Scikit-learn   | Anomaly detection using Isolation Forest |
| SQLite         | SQL-based data analysis                  |
| Pytest         | Automated testing                        |
| Ruff           | Code quality checks                      |

## Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd dataguard-ai
```

Replace `<your-repository-url>` with the actual GitHub repository URL.

### 2. Create a virtual environment

Make sure Python 3.12 is installed.

```powershell
py -3.12 -m venv .venv
```

### 3. Install the dependencies

On Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Run the application

```powershell
.\.venv\Scripts\python.exe -m streamlit run app/main.py
```

Open the local address shown in the terminal, usually:

http://localhost:8501

If Windows blocks the virtual environment inside the project folder, you can create one in another permitted location and use its Python executable instead.

## Datasets

I used two publicly available datasets from the UCI Machine Learning Repository to test the application.

### Online Retail Dataset

Contains real transaction records from an online retailer.

I used it to explore:

- Missing customer information
- Duplicate transactions
- Invalid or unusual values
- Sales and transaction patterns
- Data quality rules

### Wine Quality Dataset

Contains physicochemical measurements of red and white wines.

I used it to:

- Explore numerical features
- Visualize distributions and correlations
- Detect unusual observations using Isolation Forest

**Dataset sources:**

- [Online Retail — UCI](https://archive.ics.uci.edu/dataset/352/online+retail)
- [Wine Quality — UCI](https://archive.ics.uci.edu/dataset/186/wine+quality)

Both datasets are provided under CC BY 4.0. The repository includes smaller samples so the application can be explored without downloading the full datasets.

## How It Works

Using DataGuard AI is straightforward:

1. **Load a dataset:** Choose one of the included samples or upload your own CSV file.
2. **Explore the data:** Review columns, data types, missing values, and distributions.
3. **Check data quality:** Identify potential issues using configurable validation rules.
4. **Detect anomalies:** Run Isolation Forest to flag unusual numerical observations.
5. **Clean the data:** Preview transformations before applying them.
6. **Analyze and export:** Use SQL queries and download the results.

Anomaly detection is intended to support investigation. A flagged observation is not necessarily an error, and the application does not automatically delete anomalies.

## Testing

I tested the project using automated tests and a local browser workflow.

**Results:**

- 88 automated tests passed
- Data loading and validation checked
- Cleaning operations and transformation history tested
- Anomaly detection reproducibility checked
- SQL analytics and exports tested
- Streamlit navigation and application workflows verified

To run the tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Current Limitations

DataGuard AI is a portfolio project, not a production data management platform.

A few things to keep in mind:

- Anomaly detection identifies unusual observations, not confirmed errors.
- The quality score is a helpful summary, but individual issues still need review.
- Interactive uploads and model execution have size limits.
- Session data is temporary, so results should be exported before leaving.
- The application does not include user authentication or permanent data storage.

For public deployments, use non-sensitive datasets.

## Future Improvements

Some features I'd like to explore next:

- More customizable data quality rules
- Additional anomaly detection methods
- Better comparison of datasets before and after cleaning
- Saved analysis sessions
- More advanced reporting and dashboards

## About This Project

I developed DataGuard AI as a hands-on project to strengthen my skills in **Data Analytics, Python, Machine Learning, and Business Intelligence**.

Rather than working only with clean datasets, I wanted to build something that addresses a common challenge in real data projects: understanding and improving data quality before drawing conclusions.

This project gave me practical experience with data validation, exploratory analysis, anomaly detection, SQL, application development, and automated testing.

## License

The application code is available under the [MIT License](LICENSE).

The included UCI dataset samples are provided under [CC BY 4.0](data/LICENSE_DATA.md), with attribution to their original authors.
