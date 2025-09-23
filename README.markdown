# Enumerator Daily Survey Productivity Tool

A Streamlit app to generate daily survey count sheets from `.dta` or `.xlsx` files, split by enumerator and optional village, with 'Yes' and 'No' consent rows. Includes a total column and customizable date header styles for Excel output.

## Features
- Upload `.dta` (Stata) or `.xlsx` (Excel) files
- Automatically apply enumerator labels for `.dta` files (use 'enum' or 'enum_lab')
- Map columns for consent, enumerator, village (optional), and field date
- Choose from four date header styles: Pretty, Safe, Compact, or ISO
- Download results as an Excel file with daily counts and totals
- Minimalistic and polished UI

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/survey-productivity-tool.git
   cd survey-productivity-tool
   ```

2. **Create a virtual environment** (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**:
   ```bash
   streamlit run app.py
   ```

5. Open your browser to `http://localhost:8501`.

## Dependencies
See `requirements.txt` for the list of required Python packages.

## Usage
1. Upload a `.dta` or `.xlsx` file containing survey data.
2. Select the column mappings for Consent, Enumerator, Village (optional), and Field Date.
3. Choose a date header style for the Excel output.
4. View the preview table and download the processed data as an Excel file.

## Notes
- Ensure your data includes columns for consent (e.g., 1/0, yes/no), enumerator, field date, and optionally village.
- The app handles duplicate column names and missing data with appropriate warnings.
- For `.dta` files, value labels are applied automatically if available.

## License
MIT License