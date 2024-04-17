import pandas as pd
import datetime
import numpy as np
import sys
import openpyxl

class CallCenterMetrics:
    
    def __init__(self, data_paths, start_date, end_date):
        """
        Initializes the WeeklyMetrics class with file paths and date information.

        Args:
            self (CallCenterMetrics): An instance of the CallCenterMetrics class.
            data_paths (dict): A dictionary containing file paths for each DataFrame.
                Keys should be descriptive names (e.g., 'call_center_data', 'dials_data').
                Values should be the corresponding file paths.
            start_date (str): Start date in YYYY-MM-DD format.
            end_date (str): End date in YYYY-MM-DD format.

        Raises:
            ValueError: If any of the required keys are missing from the data_paths dictionary.
        """
        
        required_keys = ['call_center_data', 'dials_data', 'contacts_data', 'five9_data', 'paylocity_data']
        if not all(key in data_paths for key in required_keys):
            raise ValueError(f"Missing required keys in data_paths: {', '.join(set(required_keys) - set(data_paths.keys()))}")

        self.dataframes = {}
        for key, path in data_paths.items():
            self.dataframes[key] = pd.read_csv(path)

        # Read paylocity data with no header
        self.payloc_df = pd.read_csv(data_paths['paylocity_data'], header=None)

        # Store start and end dates
        self.start_date = start_date
        self.end_date = end_date
        
    
    def calculate_sets(self):
        """
        Calculates the number of sets for each agent within a specified date range.

        This method identifies rows where the 'WT/SA Bonus' is not equal to '$0.00' 
        (indicating completed sets) within the provided date range. It then counts the 
        occurrences of these completed sets for each agent (case-insensitively).

        Args:
            self (CallCenterMetrics): An instance of the CallCenterMetrics class.

        Returns:
            pandas.DataFrame: A DataFrame containing agent names (lowercase) and their 
                            corresponding set counts.
        """

        calls_df = self.dataframes['call_center_data']
        # Filter to date range
        calls_df['Call Date'] = pd.to_datetime(calls_df['Date/Time']).dt.normalize()
        date_mask = (calls_df['Call Date'] >= self.start_date) & (calls_df['Call Date'] <= self.end_date)
        filtered_data = calls_df.loc[date_mask]

        # Identify completed sets based on bonus and count occurrences per agent
        completed_sets = filtered_data[filtered_data['WT/SA Bonus'] != '$0.00']
        agent_sets = completed_sets['BCI Caller'].str.lower().value_counts().reset_index()

        # Standardize names
        name_mapping = {'mperez': 'ysanchez', 'mgarcia': 'ysanchez'}
        agent_sets['AGENT'] = agent_sets['BCI Caller'].apply(lambda x: name_mapping.get(x, x))

        # Rename columns for relational joins
        agent_sets = agent_sets.rename(columns={'count': 'Sets'})[['AGENT', 'Sets']]
        
        return agent_sets
        
    def calculate_contacts(self):
        """
        Calculates the number of contacts for each agent within the contacts DataFrame.

        This method extracts agent usernames from the 'AGENT' column by splitting on the "@" symbol.
        It then sums the values in columns starting from the 4th position (assuming these represent contact attempts).
        Finally, it merges the resulting DataFrame containing agent names and total contacts with the DataFrame returned 
        by the `sets_manip` function, ensuring both DataFrames have a matching 'AGENT' column.

        Args:
            self (CallCenterMetrics): An instance of the CallCenterMetrics class.

        Returns:
            pandas.DataFrame: A DataFrame containing agent names and their corresponding total contact counts, 
                                merged with the output of the `sets_manip` function.
        """

        # Extract agent usernames and calculate total contacts
        contacts_df = self.dataframes['contacts_data']
        contacts_df['AGENT'] = contacts_df['AGENT'].str.split('@').str[0]

        # Calculate total contacts on list of numeric columns
        numeric_columns = contacts_df.select_dtypes(include=[np.number])
        contact_cols = numeric_columns.dropna(axis=1, how='all').columns.to_list()
        contacts_df['Contacts'] = contacts_df[contact_cols].sum(axis=1)

        # Merge with DataFrame from calculate_sets
        contact_summary = contacts_df[['AGENT', 'Contacts']]
        merged_df = contact_summary.merge(self.calculate_sets(), on='AGENT', how='inner')

        return merged_df
        
    def calculate_dials(self):
        """
        Calculates the number of dials for each agent within the dials DataFrame 
        and merges it with the results from calculate_contacts and calculate_sets functions.

        This method removes the 'AGENT GROUP' column, extracts agent usernames from 'AGENT', 
        calculates the sum of all columns (representing dials), and selects relevant columns 
        for the final DataFrame. It then merges this DataFrame with the outputs from 
        `calculate_contacts` and `calculate_sets` functions based on the matching 'AGENT' column.

        Finally, it calculates the 'Sets/Dial' and 'Sets/Contact' ratios (assuming 'Sets' is 
        the number of completed sets) using vectorized operations for efficiency.

        Args:
            self (CallCenterMetrics): An instance of the CallCenterMetrics class.

        Returns:
            pandas.DataFrame: A DataFrame containing agent information, total dials, 
                                contacts, sets, sets/dial ratio, and sets/contact ratio.
        """
        
        dials_df = self.dataframes['dials_data']
        # Clean and extract agent information
        dials_df.drop(columns={'AGENT GROUP'}, inplace=True)
        dials_df['AGENT'] = dials_df['AGENT'].str.split('@').str[0]

        # Calculate total dials on list of numeric columns
        numeric_columns = dials_df.select_dtypes(include=[np.number])
        dial_cols = numeric_columns.dropna(axis=1, how='all').columns.to_list()
        dials_df['Dials'] = dials_df[dial_cols].sum(axis=1)

        # Merge with DataFrame from calculate_contacts
        dials_summary = dials_df[['AGENT', 'AGENT FIRST NAME', 'AGENT LAST NAME', 'Dials']]
        merged_df = self.calculate_contacts().merge(dials_summary, on='AGENT', how='inner')
        
        merged_df['AGENT FIRST NAME'] = merged_df['AGENT FIRST NAME'] + ' ' + merged_df['AGENT LAST NAME'].str[0]
        merged_df['Sets/Dial'] = round((merged_df['Sets'] / merged_df['Dials']) * 100, 2)
        merged_df['Sets/Contact'] = round((merged_df['Sets'] / merged_df['Contacts']), 2)

        return merged_df
        
    def calculate_five9_calling_hours(self):
        """
        Calculates the total calling hours spent by each agent based on 'On Call' and 'Ready' states in the Five9 data.

        This method splits the 'On Call / AGENT STATE TIME' and 'Ready / AGENT STATE TIME' columns 
        into separate hour, minute, and second columns. It then converts the minutes and seconds 
        into fractional hours and sums them for each state ('On Call' and 'Ready'). Finally, it calculates 
        the total calling hours by summing these state durations and extracts agent usernames.

        Args:
            self (CallCenterMetrics): An instance of the CallCenterMetrics class.

        Returns:
            pandas.DataFrame: A DataFrame containing agent names and their corresponding total calling hours.
        """
        
        hours_df = self.dataframes['five9_data']
        # Split time strings into separate columns and convert to numeric
        time_cols = ['On Call / AGENT STATE TIME', 'Ready / AGENT STATE TIME']
        for col in time_cols:
            hours_df[[f'{col} hour', f'{col} min', f'{col} sec']] = hours_df[col].str.split(":", expand=True).astype(float)

        # Group by agent and sum time components
        time_cols_expanded = hours_df[[
            'AGENT','On Call / AGENT STATE TIME hour', 'On Call / AGENT STATE TIME min', 
            'On Call / AGENT STATE TIME sec','Ready / AGENT STATE TIME hour', 'Ready / AGENT STATE TIME min', 
            'Ready / AGENT STATE TIME sec'
        ]]
        agent_times = time_cols_expanded.groupby('AGENT').sum()

        # Convert minutes and seconds to fractional hours
        agent_times['On Call Minutes'] = agent_times['On Call / AGENT STATE TIME min'] / 60
        agent_times['On Call Seconds'] = agent_times['On Call / AGENT STATE TIME sec'] / (60 * 60)
        agent_times['Ready Minutes'] = agent_times['Ready / AGENT STATE TIME min'] / 60
        agent_times['Ready Seconds'] = agent_times['Ready / AGENT STATE TIME sec'] / (60 * 60)

        # Calculate total time for each state and overall calling hours
        agent_times['Total On Call Time'] = round(agent_times['On Call / AGENT STATE TIME hour'] + agent_times['On Call Minutes'] + agent_times['On Call Seconds'], 2)
        agent_times['Total Ready Time'] = round(agent_times['Ready / AGENT STATE TIME hour'] + agent_times['Ready Minutes'] + agent_times['Ready Seconds'], 2)
        agent_times['Five9 Calling Hours'] = agent_times['Total On Call Time'] + agent_times['Total Ready Time']

        # Prepare final DataFrame
        hours_summary = agent_times.reset_index()
        hours_summary['AGENT'] = hours_summary['AGENT'].apply(lambda x: x.split("@")[0])
        hours_summary = hours_summary[['AGENT', 'Five9 Calling Hours']]

        return hours_summary

    
    def calculate_set_ratio(self):
        """
        Calculates and rounds agent call activity and merges them into a final DataFrame.

        This function merges the outputs from `calculate_dials` and `calculate_five9_calling_hours` functions 
        based on the 'AGENT' column. It then selects specific columns, rounds certain metrics (Sets/Dial, Sets/Contact), 
        and creates new columns for a custom rounding logic applied to Five9 Calling Hours. Finally, it calculates 
        Sets/Five9 Calling Hours and returns the final DataFrame.

        Args:
            self (CallCenterMetrics): An instance of the CallCenterMetrics class.

        Returns:
            pandas.DataFrame: A DataFrame containing agent information, call metrics, and rounded values.
        """
        
        # Merge DataFrames and select relevant columns
        merged_df = self.calculate_dials().merge(self.calculate_five9_calling_hours(), on='AGENT', how='inner')
        export_df = merged_df[['AGENT FIRST NAME', 'Dials', 'Contacts', 'Sets', 'Sets/Dial', 'Sets/Contact', 'Five9 Calling Hours']]
        
        # Round specific metrics
        export_df = export_df.round({'Sets/Dial': 2, 'Sets/Contact': 2, 'Five9 Calling Hours': 2})

        # Extract integer part and fractional part of time
        export_df['Hours'] = export_df['Five9 Calling Hours'].astype(int)
        export_df['Minutes'] = (export_df['Five9 Calling Hours'] % 1 * 100).round(0).astype(int)

        # Round minutes
        rounding_tiers = {
            (0, 15): 0,
            (15, 40): 0.25,
            (40, 65): 0.50,
            (65, 90): 0.75,
            (90, float('inf')): 1.0
        }
        rounding_tiers_list = [(low, high, rounding_tiers[(low, high)]) for low, high in rounding_tiers.keys()]
        export_df['Rounded Minutes'] = export_df['Minutes'].apply(
            lambda x: 
                next((round_, None) for low, high, round_ in rounding_tiers_list if low <= x < high)[0]
        )

        # Combine hours and rounded minutes for Five9 Calling Hours
        export_df['Five9 Calling Hours (Rounded)'] = export_df['Hours'] + export_df['Rounded Minutes']

        # Calculate Sets/Five9 Calling Hours
        export_df['Sets/Five9 Calling Hours'] = export_df['Sets'] / export_df['Five9 Calling Hours (Rounded)']
        export_df.drop(columns={'Minutes', 'Rounded Minutes'}, inplace=True)

        return export_df
    
    def find_paylocity_working_hours(self):
        """
        Processes the paylocity data to extract agent names and working hours.

        This function gathers rows with NaN values in a specific column (index 4), extracts hours from those rows 
        (handling potential conversion errors), creates a new DataFrame with identified agents and their working hours, 
        parses agent names based on patterns ("ID:"), cleans and formats first names and last initials, and returns 
        a DataFrame with 'AGENT FIRST NAME' and 'Paylocity Working Hours' columns. This function may cause errors 
        due to the data format.

        Args:
            self (CallCenterMetrics): An instance of the CallCenterMetrics class.

        Returns:
            pandas.DataFrame: A DataFrame containing agent names and their working hours.
        """

        # Find rows with NaN values
        nan_mask = self.payloc_df.isnull()
        rows_with_nan = self.payloc_df[nan_mask.any(axis=1)]

        # Extract potential hours from NaN rows
        hours = []
        for value in rows_with_nan.iloc[:, 4]:
            try:
                if pd.notna(value):
                    hours.append(float(value))
            except ValueError:
                pass

        # Filter valid hours (excluding NaNs)
        valid_hours = [h for h in hours if pd.notna(h)] 

        # Find agents based on "ID:" pattern in the first column
        self.payloc_df.iloc[:, 0] = self.payloc_df.iloc[:, 0].astype(str)
        agents = self.payloc_df[self.payloc_df.iloc[:, 0].str.contains("ID:")][1].to_list()

        # Create DataFrame with identified agents and hours
        total_df = pd.DataFrame({'Agents': agents, 'Paylocity Working Hours': valid_hours})

        # Clean and format names (consider using regular expressions or parsing libraries)
        total_df['first_name'] = total_df['Agents'].str.split(',').str[1].str.lower().str.slice(1).str.capitalize()
        total_df['last_initial'] = total_df['Agents'].str[0]
        name_map = {'Ally': 'Allison', 'Mike': 'Michael', 'Matt': 'Matthew'}
        total_df['first_name'] = total_df['first_name'].apply(lambda x: name_map.get(x, x)) 

        # Combine first name last initial 
        total_df['AGENT FIRST NAME'] = total_df['first_name'] + ' ' + total_df['last_initial']
        total_df[['AGENT FIRST NAME', 'Paylocity Working Hours']] = total_df[['AGENT FIRST NAME', 'Paylocity Working Hours']].astype(str)
        payloc_df_merge = total_df[['AGENT FIRST NAME', 'Paylocity Working Hours']]

        return payloc_df_merge
        
    def consolidate_and_export_data(self):
        """
        Merges DataFrames, calculates ratios/averages/totals, handles NaNs, formats output, and exports to Excel.

        This function merges the results from 'hours_merge_and_round' and 'payloc_manip' DataFrames, calculates 
        ratios (e.g., Five9 Calling Hours/Paylocity Working Hours), computes means/sums for each column, handles 
        potential NaNs, formats specific columns for display, and exports the resulting DataFrame to an Excel file.

        Args:
            self (CallCenterMetrics): An instance of the CallCenterMetrics class.

        Returns:
            pandas.DataFrame: The final processed and formatted DataFrame.
        """
        
        export_df = self.calculate_set_ratio().merge(self.find_paylocity_working_hours(), on='AGENT FIRST NAME', how='outer')

        # Calculate ratio
        denominator = export_df['Paylocity Working Hours'].astype(float)
        export_df['Five9 Calling Hours/Paylocity Hours'] = (export_df['Five9 Calling Hours'] / denominator) * 100

        # Sort and round
        export_df.sort_values(by='Sets', ascending=False, inplace=True)
        export_df['Five9 Calling Hours/Paylocity Hours'] = export_df['Five9 Calling Hours/Paylocity Hours'].apply(
            lambda x: f"{round(x, 2)}%" if pd.api.types.is_numeric_dtype(x) else x)
        export_df = export_df.round({'Sets/Dial': 2,'Sets/Contact': 2, 'Five9 Calling Hours': 2, 'Sets/Five9 Calling Hours': 2})
            
        # Export to Excel file
        return export_df.to_excel(f'agent_call_center_metrics_{self.start_date.date()}_{self.end_date.date()}.xlsx', index=False)

def validate_date(date_str, format='%Y-%m-%d'):
    try:
        date_obj = pd.to_datetime(date_str, format=format)
        return date_obj
    except (ValueError, pd.errors.OutOfBoundsDatetime):
        print(f"{date_str} is not a valid date in the format '{format}'. Please try again.")


def main():
    """
    Main function to demonstrate CallCenterMetrics usage.
    """
    
    data_paths = {
        'call_center_data': 'data/call_center_master_list.csv',
        'dials_data': 'data/total_warm_dials.csv',
        'contacts_data': 'data/total_warm_contacts.csv',
        'five9_data': 'data/agent_daily_summary.csv',
        'paylocity_data': 'data/master_timecard_summary.csv'
    }

    start_date = validate_date(date_str=sys.argv[1])
    end_date = validate_date(date_str=sys.argv[2])

    inst = CallCenterMetrics(data_paths=data_paths, start_date=start_date, end_date=end_date)
    inst.consolidate_and_export_data()

if __name__ == "__main__":
    main()
