# Load Forecasting in Smart Grids

## Overview
This project implements **load forecasting** using **quadratic regression** to predict electricity demand based on temperature variations. The approach is applied in the context of **smart grids**, where accurate forecasting helps in optimizing energy distribution and grid efficiency.

## Methodology
- **Quadratic Regression Model**: Used to capture both **linear and non-linear** relationships between temperature and electricity load.
- **Training Period**: The model is trained on **2019-2023 data** to compute regression coefficients.
- **Prediction Period**: The model is applied to **2014-2018 data** for validation.
- **Dynamic Slicing**: The forecasting task is distributed across three servers:
  - **Server 1 (Jan-Apr)**
  - **Server 2 (May-Aug)**
  - **Server 3 (Sep-Dec)**
- **Partial Verification**: A randomly selected month from each server's forecast is re-computed and validated.

## Model Equation
The quadratic regression model follows the equation:

\[
\text{Load} = β_0 + β_1 \times \text{Temperature} + β_2 \times \text{Temperature}^2
\]

where:
- **β0**: Intercept
- **β1**: Linear coefficient
- **β2**: Quadratic coefficient

The coefficients are computed using **Ordinary Least Squares Estimation (OLSE)**.

## How to Use

***Step 1️⃣: Clone the Repository***

To download the project, clone it from GitHub:
git clone https://github.com/YOUR_USERNAME/Load_Forecasting.git

***Step 2️⃣: Install Dependencies***

Ensure you have Python installed, then install the required packages:
pip install pandas scikit-learn numpy matplotlib

***Step 3️⃣: Run the Model***

Step 1: Train the Model
Run the script to train the quadratic regression model and compute coefficients:
python experiment.py
Step 2: Forecast Load
The script will automatically apply the trained model to predict load for 2014-2018.
Step 3: Verify Predictions
The script will perform partial verification by re-computing predictions for a randomly selected month.

***Step 4: Output***
After running the script:
Predicted load values will be displayed.
Execution times for each server and verification will be printed.



## License
This project is licensed under the **MIT License**.


### MIT License

Copyright (c) [2025] [CrySPR-Lab]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
