# Agent Call Center Script

The Agent Call Center Script is a Python script designed to consolidate data from various sources, including Google, Five9, and Paylocity, into a unified tabular format or report. This report provides insights into agent performance metrics such as dials, contacts, sets, working hours, calling hours, and more. By analyzing this data, BCI can gain a better understanding of how agents allocate their time and assess their effectiveness.

<br>

# Breakdown: Running the Script with Docker

This guide provides step-by-step instructions on how to run the Python script using Docker. It assumes you have a Dockerfile and a `run.sh` file in your GitHub repository.

## **Prerequisites:**

* **Git**: Download and install Git from [https://git-scm.com/](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) if you don't have it already.
* **Docker Desktop**: Download and install Docker Desktop from [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/).

## **Steps:**

### **1. Clone the Repository:**

Open a terminal window and use the `git clone` command to clone the GitHub repository to your local machine. Replace `<username>` and `<repository_name>` with your actual details. 

More info here [https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)

```bash
git clone https://github.com/<username>/<repository_name>.git
```

### **2. Navigate to the Cloned Repository:**

```bash
cd agent_performance
```

### **3. Prepare the data:**

<b>CSV Files</b>:
- Location: The script expects five CSV files to be present in the `data/` directory within your project directory. Example files are included in the `data/` dir
  
- File Names:
  
  - `call_center_csv`: The call center master leads list downloaded from Google Spreadsheets
  - `dials_csv`: Total dials CSV downloaded from Five9
  - `contacts_csv`: Total contacts CSV downloaded from Five9
  - `five9_csv`: Agent daily state summary CSV downloaded from Five9
  - `paylocity_csv`: Master time card summary CSV automatically sent weekly by Paylocity

<b>Date Range</b>:
- The script will prompt you to enter the `start_date` and `end_date` in YYYY-MM-DD format for the report generation
- Ensure the data within the CSV files covers the specified date range
- Maintain consistent file names as above across script executions to avoid errors
- The script relies on these specific names to locate and process the data

### **4. Run the shell (.sh) file**

```bash
sh run.sh
```

This script prompts the user for the `start_date` and `end_date`, builds a Docker image, and runs the Python script (report_script.py) within the container, passing the validated dates as arguments.

Key Points:

- Validates dates in YYYY-MM-DD format
- Builds call_metrics_image from Dockerfile
- Runs a container with volume mounting for script access
- Executes report_script.py with validated dates
- Returns a flat tabular file, combining call center metrics with agent activity data


### Output

The shell command will generate `agent_call_center_metrics_{startdate}_{enddate}.xlsx` in your working directory

Which we can open, resize, save, and distribute.

<div style="text-align: center;">
  <img width="971" alt="Screenshot 2022-06-26 at 12 58 47 PM" src="https://user-images.githubusercontent.com/47290536/175829815-8943e422-e346-4926-a722-1000e4a777e3.png">
</div>

<br>


Ex.
```bash
! cd Desktop/
! git clone https://github.com/murdockma/agent_performance.git
! cd agent_performance/

# Ensure data files are in the /data dir
! sh run.sh
```

<br>

## Technical Details

### Docker Implementation
Docker provides a way to package your Python script and its dependencies into a self-contained unit. This allows you to run your script in a consistent environment regardless of the host machine's configuration.

The provided shell commands used in the project demonstrate how to build and run the Docker image:

### **Building the Image:**

```bash
docker build -t call_metrics_image .
```
This command builds a Docker image based on the instructions in your Dockerfile. The -t option tags the image with a name call_metrics_image for easy reference. The . at the end specifies the context (current directory) where the Dockerfile resides.
  
### ***Running the Container:***
```bash
docker run -it --rm --name my-container -v $(pwd):/app call_metrics_image python /app/report_script.py "$start_date" "$end_date"
```
This command runs the built image and executes the specified command:
  
  `-it`: Runs the container in interactive mode and allocates a pseudo-TTY
  
  `--rm`: Removes the container automatically after it exits
  
  `--name my-container`: Assigns a name (my-container) to the container for easier identification.
  
  `-v $(pwd):/app`: Mounts the current directory ($(pwd)) of your local machine onto the /app directory within the container. This allows you to easily update your script and data files without rebuilding the image.
  
  `call_metrics_image`: Specifies the name of the Docker image to run.
  
  `python /app/report_script.py "$start_date" "$end_date"`: Executes the Python script (report_script.py) within the container, passing the start_date and end_date arguments as specified.

### Script Methods</b>

This class handles data processing and analysis for call center metrics. Here's a detailed explanation of each method:

**1. `init(self, data_paths, start_date, end_date)`:**

Initializes the class with file paths for various CSV data sources and the date range for the report.
Validates if all required keys (call_center_data, etc.) are present in the data_paths dictionary.
Stores dataframes loaded from CSV files (dataframes dictionary) with the exception of the Paylocity data (payloc_df), which is read without headers.
Stores the provided start and end dates (start_date, end_date).

**2. `calculate_sets(self)`:**

Calculates the number of completed sets (identified by non-zero "WT/SA Bonus") within the date range for each agent in the call_center_data DataFrame.
Filters data based on the date range.
Groups data by agent (BCI Caller) and counts occurrences of completed sets (case-insensitively).
Applies name mapping for consistency (name_mapping).
Renames columns for future joins (AGENT).
Returns a DataFrame containing agent names and corresponding set counts.


**3. `calculate_contacts(self)`:**

Calculates the total number of contacts attempted by each agent in the contacts_data DataFrame.
Extracts agent usernames by splitting the AGENT column on "@".
Calculates the sum of values in all numeric columns (assumed to represent contact attempts).
Merges the resulting DataFrame (contact_summary) with the output from calculate_sets based on the matching AGENT column.
Returns the merged DataFrame containing agent names, total contacts, and set counts.

**4. `calculate_dials(self)`:**

Calculates the number of dials made by each agent in the dials_data DataFrame and merges it with previous results.
Removes unnecessary columns (AGENT GROUP).
Extracts agent usernames from the AGENT column.
Calculates the sum across all numeric columns (assumed to represent dials).
Merges the resulting DataFrame (dials_summary) with the merged output from previous functions based on AGENT.
Calculates ratios like Sets/Dial and Sets/Contact using vectorized operations.
Returns a DataFrame containing agent information, dials, contacts, sets, and calculated ratios.


**5. `calculate_five9_calling_hours(self)`:**

Calculates the total calling hours spent by each agent based on "On Call" and "Ready" states in the five9_data DataFrame.
Splits time strings in relevant columns ("On Call / AGENT STATE TIME", etc.) into separate hour, minute, and second columns.
Converts minutes and seconds to fractional hours and sums them for each state.
Calculates total calling hours by summing state durations.
Extracts agent usernames.
Returns a DataFrame containing agent names and total calling hours.

**6. `calculate_set_ratio(self)`:**

Merges outputs from calculate_dials and calculate_five9_calling_hours based on AGENT.
Selects relevant columns and rounds specific metrics (Sets/Dial, Sets/Contact).
Creates separate columns for integer and fractional parts of Five9 Calling Hours.
Implements custom rounding logic for minutes based on predefined tiers in a dictionary.
Combines hours and rounded minutes for a new "Five9 Calling Hours (Rounded)" column.
Calculates the ratio Sets/Five9 Calling Hours (Rounded).
Returns the final DataFrame with various call activity metrics and rounded values.

**7. `find_paylocity_working_hours(self)`:**

Processes the Paylocity data (payloc_df) to extract agent names and working hours.
Identifies rows with NaN values in a specific column (index 4).
Attempts to extract hours from those rows, handling potential conversion errors.
Filters valid hours (excluding NaNs).
Finds agents based on patterns ("ID:") in the first column.
Creates a DataFrame with identified agents and working hours.
Cleans and formats first names and last initials (consider using regular expressions for better name parsing).
Combines first name and last initial into a new column AGENT FIRST NAME.
Returns a DataFrame containing agent names and their working hours.
