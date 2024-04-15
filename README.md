# Breakdown
This Python script - `agent_call_center_metrics.py`, generates a flat tabular file, combining call center metrics with agent activity data. It requires seven mandatory parameters:

- <b>CSV Files</b>:
  - `call_center_csv`: The call center master leads list downloaded from Google Spreadsheets
  - `dials_csv`: Total dials CSV downloaded from Five9
  - `contacts_csv`: Total contacts CSV downloaded from Five9
  - `five9_csv`: Agent daily state summary CSV downloaded from Five9
  - `paylocity_csv`: Master time card summary CSV automatically sent weekly by Paylocity

- <b>Date Range</b>:
  - `start_date`: Enter the start date in YYYY-MM-DD format
  - `end_date`: Enter the end date in YYYY-MM-DD format
  

<br>

## Running the Script (MacOS) 𐭁

1. Prerequisites:
   - <b>Developer Tools</b>: Open your terminal and run `xcode-select --install` to install developer tools if needed
   - <b>Git</b>: If you don't have Git, install it following instructions you can find online (on Mac, Git is included with developer tools).

2. Clone the Repository:
   - If the script isn't in your current directory, clone the repository containing the script using the following command `git clone https://github.com/murdockma/agent_performance.git`

4. Navigate to the Script Directory:

   Use `cd agent_peformance` to enter the cloned directory

6. Install Dependencies:
   - Run `sh conf/config.sh` to install required Python libraries the script depends on. You might be prompted for your password during installation
  
7. Verify Installation:
   - Run `pip show pandas` or `pip3 show pandas` to verify pandas is installed and shows a version number
     
6. Prepare Data Files:
   - Ensure the five required CSV files are named exactly as mentioned earlier and placed in the `data/` directory
   - These file names should be consistent each time you run the script

     ![Screenshot 2022-06-26 at 12 40 57 PM](https://user-images.githubusercontent.com/47290536/175829250-06beeaa3-f698-44c8-be32-48d4d50e3734.png)
     

7. Run the Script:
   - In your terminal, type python `agent_call_center_metrics.py` to execute the script
   - The script will prompt you to enter the start and end dates for the desired week in YYYY-MM-DD format

### Output

If successful, the script generates a weekly metrics report as an Excel file named `agent_call_center_metrics_{startdate}_{enddate}.xlsx` in your working directory

Which we can open, resize, save, and distribute.

<div style="text-align: center;">
  <img width="971" alt="Screenshot 2022-06-26 at 12 58 47 PM" src="https://user-images.githubusercontent.com/47290536/175829815-8943e422-e346-4926-a722-1000e4a777e3.png">
</div>

<br>

## Technical Details

### Script Methods</b>

The script utilizes seven internal methods to process and transform data:
 
 - `sets_manip` 
     - Calculates the number of sets per agent. The method preserves the agents username and # of sets (a set is calculated as a row that does not have a 'WT/SA Bonus' of $0). Within this method, we are also manually changing certain agents usernames, given that some agents have different usernames across datasets (this is more of a data integrity issue, that would need to be fixed on the source end). <b>Final output is a dataframe consisting of agents and their # of sets </b>.
 - `contacts_manip`
     - Sums the columns across each row (i.e, agent) to calculate dials. This method also merges its output with the previous method, sets_df. <b>Final output is a dataframe consisting of agent usernames, and there respective number of sets and contacts</b>.
 - `dials_manip` 
     - Almost identical to contacts_manip, except it calculates total agent dials, and also does some feature engineering on columns to produce new columns like sets/dial, and sets/contact. <b>Final output is a dataframe consisting of agents (including their first/last name) and their # of dials, sets, contacts, sets/dials, and sets/contacts</b>.
 - `five9_manip` 
     - Splits datetime object into hours. <b>Final output is a dataframe consisting of agents and their total five9 working hours (i.e, whole number+fractional amount of hours [<i>e.g, 40.267</i>] )</b>.
 - `hours_merge_and_round` 
     - Brings together previous datasets with the five9 hours, returning each agent and their total five9 working hours. This method also rounds the agents fractional hours into either .00, .25, .50, .75, or 1.0. <b>Final output is a dataframe consisting of agents and all previous data + each agents total five9 hours</b>
 - `payloc_manip`
     - Cumulates multiple columns on hours into a summed row per agent. Within this method we are also manually changing agents usernames to match across datasets. <b>Final output of this method is each agent and their total paylocity working hours</b>
 - `clean_and_export` 
     - Method that merges all previous data with paylocity hours, brings it all into one dataframe, does some simple clean up, and exports it to an .xlsx file. This can be changed to .csv or whatever output in desired. This method is also calculating aggregates across columns as rows, and producing new columns. <b>Final output is the weekly metrics spreadsheet</b>.


<br>
### Class Instantiation:

The script utilizes a class-based approach. To run the script, you'll need to instantiate the class named `weekly_metrics` and pass the required parameters to its constructor:

```python
inst = weekly_metrics(call_center_csv="call_center_master_list.csv",
                      dials_csv="total_warm_dials.csv",
                      contacts_csv="total_warm_contacts.csv",
                      five9_csv="agent_daily_summary.csv",
                      paylocity_csv="master_timecard_summary.csv",
                      start_date = "2022-03-01",
                      end_date="2022-03-05")
```
                  
This assigns the instantiated object to a variable (`inst`). You can then call the `final_merge` method of the object to generate the final .xlsx file

```python
inst.final_merge()
```

<br>

## Enhancements: The Road Ahead

This script holds promise for significant improvement in three key areas: logic, data access, and user experience. Here's a breakdown of potential advancements:

  - <b>Logic Enhancements</b>: The script's logic can be refined to handle more complex scenarios and generate even more insightful reports. This might involve incorporating additional data points or implementing advanced data analysis techniques

  - <b>Data Accessibility</b>: Currently, the script relies on manually placing CSV files in a specific location. A significant improvement would be to have it retrieve data directly from APIs (Application Programming Interfaces) provided by the data sources (Five9, Paylocity, etc.). This would eliminate manual file handling and streamline the process
    
    - <b>Improved Usability</b> - Here's how API integration can improve the script's usability:
     
      - <b>Separate Data Fetching Scripts</b>: Create individual Python scripts dedicated to fetching data from each API endpoint. This modular approach promotes code organization and reusability.
        
      - <b>Autonomous Script</b>: By incorporating the separate data fetching scripts and calling them within the main script, you can achieve a fully autonomous script. This eliminates manual file management and simplifies the execution process.
        
      - <b>Effortless Usage</b>: As long as the API endpoints remain functional and data structures consistent, the script becomes incredibly user-friendly. Users can simply run the script without needing to worry about manual file handling.

  - <b>User Experience</b> - Here are a couple of options for improving the digestion and distribution of this report:
    
    - <b>Dashboard Integration</b>: Consider integrating the report generated by the script into a dashboarding tool. This would allow for real-time data visualization and facilitate data exploration
      
    - <b>Automated Scheduling</b>: Schedule the script to run automatically at regular intervals (daily, weekly, etc.) using cron jobs (on Linux/macOS) or Task Scheduler (on Windows)
