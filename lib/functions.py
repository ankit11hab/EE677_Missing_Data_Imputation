import numpy as np
import pandas as pd

class Functions: 
    def interpolate(self, data = None, method='linear', column='Power'):
        if data is None:
                print("Data not found in method: interpolate")
        if isinstance(data, pd.DataFrame):
            series = data[column]
        elif isinstance(data, np.ndarray):
             series = data
        else:
            print("No supported type found. Please use either a dataframe or a series to interpolate.")
            return None
        if method=='bfill':
            series = series.bfill()
        elif method=='ffill':
            series = series.ffill()
        else:
            series = series.interpolate(method=method)
        if isinstance(data, pd.DataFrame):
            data[column] = series
        return data
    
    def find_trend(self, series, order):
        coef = np.polyfit(np.arange(len(series)), series.values.ravel(), order)
        poly_mdl = np.poly1d(coef)
        trend = pd.Series(data=poly_mdl(np.arange(len(series))))
        return trend

    def detrend_data(self, data, order, column='Power'):
        interpolated_data = self.interpolate(data.copy(), method='cubic', column=column)
        interpolated_data = self.interpolate(interpolated_data, method='bfill', column=column)
        interpolated_data = self.interpolate(interpolated_data, method='ffill', column=column)
        trend = self.find_trend(interpolated_data[column], order)
        detrended = data[column].values - trend
        detrended_data = data.copy()
        detrended_data[column] = detrended.values
        detrended_data.index = data.index
        return trend, detrended_data
    
    def time_to_column(self, time):
        word = 'Power(t'
        if time>0:
            word = word+'+'+str(time)+')'
        else:
            word = word+str(time)+')'
        return word
    
    def time_set_to_columns(self, times):
        columns = []
        for time in times:
            if isinstance(time, str):
                columns.append(time)
                continue
            column = self.time_to_column(time)
            columns.append(column)
        return columns
    
    def do_power_shifts(self, data, values, column='Power'):
        for val in values:
            new_column = self.time_to_column(val)
            data[new_column] = data[column].shift(val*(-1))
        return data
    
    def findSubs(self, arr, index, subs, allsubs): 
        if index == len(arr): 
            if len(subs) >= 1: 
                allsubs.append(subs)
        else: 
            self.findSubs(arr, index + 1, subs, allsubs) 
            self.findSubs(arr, index + 1, subs+[arr[index]], allsubs)

    def generate_combinations(self, daily, seasonal):
        daily_subs = []
        seasonal_subs = []

        self.findSubs(daily, 0, [], daily_subs)
        self.findSubs(seasonal, 0, [], seasonal_subs)

        all_subs = []
        for daily_sub in daily_subs:
            for seasonal_sub in seasonal_subs:
                l = daily_sub+seasonal_sub
                all_subs.append(l)
        return all_subs
    
    def export_data(self, data, folder_path, file_prefix, rename_index_to = 'Time', power_column = 'Power'):
        data.reset_index(inplace=True)
        data.rename(columns={'index':rename_index_to}, inplace=True)
        data[power_column].fillna('NR', inplace=True)
        data[rename_index_to] = pd.to_datetime(data[rename_index_to]) 

        for date, group in data.groupby(data[rename_index_to].dt.date):
            file_name = f"{folder_path}/{file_prefix}_{date}.xlsx" 
            group.to_excel(file_name, index=False, engine='openpyxl')