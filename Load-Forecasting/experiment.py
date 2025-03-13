import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import time
import threading
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Load the main dataset for training (e.g., 2019-2023)
train_data = pd.read_csv('combined_load_temp_data_2019_2023.csv')

# Function to get coefficients by training the model
def get_model_coefficients(data):
    X_temp = data[['Temperature']]
    y_load = data['forecast_load_mw']
    model = make_pipeline(PolynomialFeatures(degree=2), LinearRegression())
    model.fit(X_temp, y_load)
    intercept = model.named_steps['linearregression'].intercept_
    coef = model.named_steps['linearregression'].coef_
    return intercept, coef

# Get coefficients from the training data for main forecasting
main_intercept, main_coef = get_model_coefficients(train_data)

# Load the "future" temperature data (2014–2018)
future_data = pd.read_csv('combined_load_temp_data_2014_2018.csv')

# Function to predict load using calculated coefficients
def predict_load(data_subset, server_name, intercept, coef, results):
    X_temp = data_subset[['Temperature']]
    start_time = time.time()
    data_subset['Predicted_Load'] = intercept + coef[1] * X_temp['Temperature'] + coef[2] * (X_temp['Temperature'] ** 2)
    execution_time = time.time() - start_time
    print(f"Execution time for {server_name}: {execution_time:.4f} seconds")
    results[server_name] = {
        "data": data_subset[['Date', 'Temperature', 'Predicted_Load']],
        "execution_time": execution_time
    }

def slice_data_for_server(start_date, end_date):
    return future_data[(future_data['Date'] >= start_date) & (future_data['Date'] <= end_date)].copy()

server_datasets = {
    "Server 1 (Jan-Apr)": slice_data_for_server('2014-01-01', '2014-04-30'),
    "Server 2 (May-Aug)": slice_data_for_server('2014-05-01', '2014-08-31'),
    "Server 3 (Sep-Dec)": slice_data_for_server('2014-09-01', '2014-12-31')
}

results = {}
threads = []

# Start threads for each server's task
for server_name, data_subset in server_datasets.items():
    thread = threading.Thread(target=predict_load, args=(data_subset, server_name, main_intercept, main_coef, results))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

verification_results = {}
selected_months = {}

# Define mapping from verification servers to main servers
verification_to_main_server_map = {
    "Verification for Server 1 (Jan-Apr)": "Server 1 (Jan-Apr)",
    "Verification for Server 2 (May-Aug)": "Server 2 (May-Aug)",
    "Verification for Server 3 (Sep-Dec)": "Server 3 (Sep-Dec)"
}

# Function for verification
def verify_load_with_main_coefficients(main_intercept, main_coef, month_data, server_name, verification_results):
    start_time = time.time()
    X_temp = month_data[['Temperature']]
    month_data['Verification_Predicted_Load'] = main_intercept + main_coef[1] * X_temp['Temperature'] + main_coef[2] * (X_temp['Temperature'] ** 2)
    execution_time = time.time() - start_time
    print(f"Execution time for {server_name}: {execution_time:.4f} seconds")
    verification_results[server_name] = execution_time

# Randomly select a month for verification from each main server's data
np.random.seed(0)

verification_datasets = {}
for server, data in server_datasets.items():
    random_month = data['Date'].str.slice(0, 7).sample(1).values[0]
    verification_data = data[data['Date'].str.startswith(random_month)].copy()
    verification_server_name = f"Verification for {server}"
    verification_datasets[verification_server_name] = verification_data
    selected_months[verification_server_name] = pd.to_datetime(random_month + "-01").strftime('%B %Y')

# Print dynamically selected months for verification
print("Selected months for verification:")
for verification_server, month in selected_months.items():
    print(f"{verification_server}: {month}")

verification_threads = []
for verification_server, month_data in verification_datasets.items():
    thread = threading.Thread(target=verify_load_with_main_coefficients, args=(main_intercept, main_coef, month_data, verification_server, verification_results))
    verification_threads.append(thread)
    thread.start()

for thread in verification_threads:
    thread.join()

# Plot Load Prediction vs Verification Load for each Verification Server
for server_name, verification_data in verification_datasets.items():
    plt.figure()
    main_server_name = verification_to_main_server_map[server_name]
    
    # Make a copy to avoid SettingWithCopyWarning
    main_server_data = results[main_server_name]["data"].copy()
    main_server_data['Date'] = pd.to_datetime(main_server_data['Date'])
    verification_data['Date'] = pd.to_datetime(verification_data['Date'])

    plt.plot(main_server_data['Date'], main_server_data['Predicted_Load'], label='Predicted Load')
    plt.plot(verification_data['Date'], verification_data['Verification_Predicted_Load'], label='Verification of Predicted Load', linestyle='--')
    plt.xlabel('Date')
    plt.ylabel('Load (MW)')
    plt.title(f'Predicted Load of {main_server_name} vs Verification ({selected_months[server_name]})')
    plt.legend()

    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=7))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45, ha='right')

    plt.tight_layout()
    plt.savefig(f'{server_name}_load_verification.png')
    plt.close()

