import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from lib.functions import Functions

class IITG_DataLoader:
    data = None

    __power_key = 'Power'

    def __init__(self, data = None):
        self.functions = Functions()
        if data is not None:
            self.data = data
        
    def __update_corrupt_power(self, row):
        # if (not type(row[self.__power_key])==str) and row[self.__power_key] > 10:
        #     return 'NR'
        if (type(row[self.__power_key])==str) and ',' in row[self.__power_key]:
            return float(row[self.__power_key].replace(',', '.'))
        else:
            return row[self.__power_key]
        
        
    def preprocess(self, data = None, interpolate = False, update=False):
        if data is None:
            if self.data is None:
                print("Data not found in method: preprocess")
                return None
            data = self.data.copy()
        # Preprocess Time Column
        data.index = pd.to_datetime(data.index)

        # Preprocess Power Column
        data[self.__power_key] = data.apply(self.__update_corrupt_power, axis=1)
        data[self.__power_key] = pd.to_numeric(data[self.__power_key], errors='coerce')

        # Sort data by Time
        
        data = data.sort_index()

        if interpolate:
            data = self.functions.interpolate(data)
            data = self.functions.interpolate(data, method='bfill')
            data = self.functions.interpolate(data, method='ffill')
        if update:
            self.data = data
        return data
    
    def set_time_as_index(self, data, time_header='Time'):
        data = data.drop_duplicates(subset=[time_header])
        data = data.set_index(time_header, drop=True)
        data.index.name = None
        return data
        
    def load(self, file_list, interpolate = False, time_header='Time', power_header='Power'):
        data = pd.DataFrame()
        for file_path in file_list:
            target_columns = [time_header, power_header]
            header_row = None
            
            df = pd.read_excel(file_path, header=None)
            for i, row in enumerate(df.values):
                row_lower = [str(cell).lower() for cell in row]  
                if all(col_name.lower() in row_lower for col_name in target_columns):
                    header_row = i
                    break  

            if header_row is not None:
                df.columns = df.iloc[header_row]
                df = df.iloc[header_row+1:][target_columns]
                data = pd.concat([data, df], ignore_index=True)
            else:
                print("Header row not found in the file:", file_path)
        data = self.set_time_as_index(data, time_header)
        data.rename(columns = {power_header:self.__power_key}, inplace=True)
        data = self.preprocess(data, interpolate)
        self.data = data
        return data
    
    def load_all(self, folder_path, interpolate = False, time_header='Time', power_header='Power',\
                 start_time=None, end_time=None):
        file_list = []
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_list.append(file_path)
        data = self.load(file_list, interpolate, time_header, power_header)
        if start_time is not None and end_time is not None:
            data = self.get_data(start_time, end_time, data)
            self.set_data(data)
        return data
    
    def get_data(self, start_time = None, end_time = None, data = None, use_month_key = False):
        if data is None:
            if self.data is None:
                print("Data not found in method: get_data")
                return None
            data = self.data.copy()
        if start_time is None and end_time is None:
            return data
        start_time = pd.to_datetime(start_time)
        end_time = pd.to_datetime(end_time)
        if use_month_key == True:
            mask = (data.index >= start_time) & (data.index <= end_time)
        else:
            mask = (data.index > start_time) & (data.index < end_time)
        data = data.loc[mask]
        return data
    
    def set_data(self, data):
        if data is not None:
            self.data = data
    
    def plot(self, start_time = None, end_time = None, data = None, type='plot', color='b'):
        if data is None:
            if self.data is None:
                print("Data not found in method: plot")
                return None
            data = self.data.copy()
        data = self.get_data(start_time, end_time, data)
        fig, ax1 = plt.subplots(figsize=(10, 6))
        # x = data[self.__time_key].values
        y = data[self.__power_key].values
        ax1.set_xlabel('Time', color='b')
        ax1.set_ylabel('Power Consumed', color='b')
        # fig=plt.figure()
        if type=='plot':
            plt.plot(y, color=color)
        elif type=='scatter':
            plt.scatter(y, color=color)
        fig.autofmt_xdate()
        # plt.show()
        return plt

    def describe(self, start_time = None, end_time = None, data = None):
        if data is None:
            if self.data is None:
                print("Data not found in method: describe")
                return None
            data = self.data.copy()
        
        data = self.get_data(start_time, end_time, data)
        shape = data.shape
        if start_time is None:
            start_time = pd.to_datetime(data.index[0])
        if end_time is None:
            end_time = pd.to_datetime(data.index[shape[0]-1])
        columns = ', '.join(data.columns)
        mean_power = data[self.__power_key].mean()
        nan_power = data[self.__power_key].isna().sum()
        table = {'Params': ['Columns', 'Shape', 'Start Time', 'End Time', 'Mean Power', 'NaN Powers'],
                'Values': [columns, shape, start_time, end_time, mean_power, nan_power]}
        return pd.DataFrame(table)
    
    def energy_consumed(self, start_time = None, end_time = None, data = None, use_monthly_data = False):
        if use_monthly_data == True:
            if data is None:
                if self.monthly_energy_data is None:
                    print("Data not found in method: energy_consumed")
                    return None
                data = self.monthly_energy_data
            data = self.get_data(start_time, end_time, data, use_month_key = True)
            return data[self.__energy_key].sum()
        if data is None:
            if self.data is None:
                print("Data not found in method: energy_consumed")
                return None
            data = self.data.copy()
        data = self.get_data(start_time, end_time, data)
        sample_points = data.index.diff().dt.total_seconds().fillna(0).cumsum().values
        mw = data[self.__power_key].values

        # Calculate the trapezoidal integration of 'MW' with respect to 'Time'
        integral = np.trapz(mw, x=sample_points) / 3600
        return integral