from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import numpy as np
import pandas as pd

class DataImputer:
    def train_test_pred_split(self, trimmed_data, train_data, input_columns, output_column='Power'):
        X_pred = trimmed_data.loc[:, input_columns].values
        X = train_data.loc[:, input_columns].values
        Y = train_data[output_column].values
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.1)
        return X_train, X_test, Y_train, Y_test, X_pred

    def trim_data(self, data, input_columns, output_column='Power', predicted_column='PredictedPower'):
        trimmed_data = data.dropna(subset=input_columns)
        train_data = trimmed_data.dropna(subset=input_columns+[output_column])
        trimmed_data = trimmed_data[trimmed_data[predicted_column].isna()]
        return trimmed_data, train_data

    def predict(self, X_train, X_test, Y_train, Y_test, X_pred):
        alg = LinearRegression()
        alg.fit(X_train, Y_train)
        if X_test is not None and Y_test is not None:
            score = alg.score(X_test, Y_test)
        else:
            score = alg.score(X_test, Y_test)
        Y_pred = alg.predict(X_pred)
        return Y_pred, score

    def fill_values(self, data, time_instants, values, predicted_column='PredictedPower'):
        count = 0
        if len(time_instants)!=len(values):
            print("Length mismatch for filling values")
            return None
        for time, value in zip(time_instants, values):
            data.loc[time, predicted_column] = value
            count+=1
        return data, count