"""Entry point for the bank recommender application"""

import pandas as pd
from taipy.gui import Gui, State, Icon, notify, navigate
import random
import numpy as np

DATA_PATH = "data/customer_data.csv"

customer_data = pd.read_csv(DATA_PATH)[:]

# Sex Pie Chart
sex_data = customer_data["sex"]
sex_count = sex_data.value_counts()
sex_chart_data = {
    "Sex": ["Male", "Female"],
    "Count": sex_count.values.tolist(),
}

# Age Histogram
age_chart_data = {"Age": customer_data["age"].to_list()}
age_options = [
    {
        "xbins": {"start": 0, "end": 100, "size": 1},
    }
]

# Province Pie Chart
province_data = customer_data["province_name"]
province_count = province_data.value_counts()
province_count = province_count.sort_values(ascending=False)
province_count_filter = province_count[:10]
province_count_filter["Other"] = province_count[10:].sum()
province_chart_data = {
    "Province": province_count_filter.index.to_list(),
    "Count": province_count_filter.values.tolist(),
}

# Income Histogram
income_chart_data = {"Income": customer_data["income"].to_list()}
income_options = [
    {
        "xbins": {"start": 0, "end": 1000000, "size": 10000},
    }
]

# Selections
selected_gender = "Both"
selected_ages = [0, 100]
selected_province = "All"
selected_incomes = [0, 1000000]
selected_seniority = [0, 150]
provinces = ["All"] + province_count.index.to_list()

product_columns = customer_data.columns[5:]
product_counts = pd.DataFrame(
    {
        "Product": product_columns[:5],
        "Count": customer_data[product_columns]
        .sum()
        .sort_values(ascending=False)
        .values.tolist()[:5],
    }
)


customer_data[product_columns] = customer_data[product_columns]
selected_data = customer_data.copy()
predicted_data = customer_data.copy()[:10]
predictions_expand = False
predictions_unique = ["None"]
counts = [0]
predicted_counts_advertising = pd.DataFrame(
    {
        "Product": predictions_unique,
        "Count": counts,
    }
)

chosen_metric = "Impressions"
data_metric = pd.DataFrame(
    {"Day": [1, 2, 3, 4, 5, 6, 7], "Metric": [0, 0, 0, 0, 0, 0, 0]}
)
properties_metric = {
    "x": "Day",
    "y": "Metric",
}


def best_product(state: State) -> None:
    """
    Filters dataset according to user selections
    Returns the five most popular products in the filtered dataset

    Args:
        state: state of the application
    """
    notify(state, "info", "Filtering data...")
    filtered_data = customer_data.copy()
    if state.selected_gender == "Male":
        filtered_data = filtered_data[filtered_data["sex"] == "H"]
    elif state.selected_gender == "Female":
        filtered_data = filtered_data[filtered_data["sex"] == "F"]
    [min_age, max_age] = state.selected_ages
    filtered_data = filtered_data[
        (filtered_data["age"] >= min_age) & (filtered_data["age"] <= max_age)
    ]
    if state.selected_province != "All":
        filtered_data = filtered_data[
            filtered_data["province_name"] == state.selected_province
        ]
    [min_income, max_income] = state.selected_incomes
    filtered_data = filtered_data[
        (filtered_data["income"] >= min_income)
        & (filtered_data["income"] <= max_income)
    ]
    [min_seniority, max_seniority] = state.selected_seniority
    filtered_data = filtered_data[
        (filtered_data["seniority_months"] >= min_seniority)
        & (filtered_data["seniority_months"] <= max_seniority)
    ]
    state.selected_data = filtered_data
    product_counts = filtered_data[product_columns].sum()
    product_counts = product_counts.sort_values(ascending=False)
    product_counts = product_counts[:5]
    state.product_counts = pd.DataFrame(
        {
            "Product": product_counts.index.to_list(),
            "Count": product_counts.values.tolist(),
        }
    )
    notify(state, "success", "Data filtered!")


def menu_fct(state: State, var_name: str, var_value: dict) -> None:
    """
    Changes the page of the application

    Args:
        - state: state of the application
        - var_name: name of the variable changed
        - var_value: value of the variable
    """
    state.page = var_value["args"][0]
    navigate(state, state.page.replace(" ", "-"))


def product_prediction(state: State) -> None:
    """
    For each row in selected data
    Get the closest neighbors in terms of age, province and income
    Get the most popular products for these neighbors
    Recommend the most popular product that the client does not have
    """
    if len(state.selected_data) >= 3000:
        notify(
            state,
            "error",
            "Please filter the data to less than 3000 rows before predicting",
        )
        return
    notify(state, "info", "Predicting best products (closest neighbors)...")
    predictions = []
    for _, row in state.selected_data.iterrows():
        age = row["age"]
        province = row["province_name"]
        income = row["income"]
        neighbors = customer_data[
            (customer_data["age"] == age)
            & (customer_data["province_name"] == province)
            & (customer_data["income"] <= income + 10000)
            & (customer_data["income"] >= income - 10000)
        ]
        # Convert to boolean
        neighbors = neighbors[product_columns].astype(int)
        neighbors_products = neighbors[product_columns].sum()
        neighbors_products = neighbors_products.sort_values(ascending=False)
        for product in neighbors_products.index:
            if row[product] == 0:
                predictions.append(product)
                break
    predicted_data = state.selected_data.copy()
    predicted_data.insert(0, "Predicted Product", predictions)
    state.predicted_data = predicted_data
    predictions = state.predicted_data["Predicted Product"].to_list()
    state.predictions_unique = list(set(predictions))[:5]
    counts = []
    for product in state.predictions_unique:
        counts.append(predictions.count(product))
    state.counts = counts
    state.predicted_counts_advertising = pd.DataFrame(
        {
            "Product": state.predictions_unique,
            "Count": state.counts,
        }
    )
    state.predicted_counts_advertising = state.predicted_counts_advertising.sort_values(
        by="Count", ascending=False
    )
    notify(state, "success", "Best products predicted!")
    state.predictions_expand = True


def launch_campaign(state: State) -> None:
    """
    Navigate to the advertising results page
    """
    notify(state, "info", "Launching advertising campaign...")
    navigate(state, "Advertising-Results")
    update_metric(state)


def update_metric(state: State) -> None:
    """
    Simulate random data for the chosen metric
    and display them
    """
    state.data_metric = pd.DataFrame({"Day": [1, 2, 3, 4, 5, 6, 7]})
    for product in state.predictions_unique:
        coefficient = random.uniform(0.5, 1.5)
        if state.chosen_metric == "Impressions":
            impressions = np.random.randint(1000, 10000, size=7)
            impressions = impressions * coefficient
            state.data_metric[product] = impressions
        elif state.chosen_metric == "Click Rate":
            click_rate = np.random.uniform(0, 0.8, size=7)
            click_rate = click_rate * (coefficient - 0.5)
            state.data_metric[product] = click_rate
        else:
            buy_rate = np.random.uniform(0, 0.2, size=7)
            buy_rate = buy_rate * (coefficient - 0.5)
            state.data_metric[product] = buy_rate
    properties = {"x": "Day"}
    for index, product in enumerate(state.predictions_unique):
        properties[f"y[{index}]"] = product
    state.data_metric = state.data_metric
    state.properties_metric = properties


page = "Popular Products"

menu_lov = [
    ("Popular Products", Icon("images/popular_products.png", "Predict Products")),
    ("Customer Data", Icon("images/customer_data.png", "Customer Data")),
    (
        "Advertising Results",
        Icon("images/advertising_results.png", "Advertising Results"),
    ),
]


def column_style(state, value):
    """
    Highlight in red products cells that are 1
    """
    if value == 1:
        return "highlight"


style_properties = {}

for product in product_columns:
    style_properties[f"style[{product}]"] = "column_style"


ROOT = """
<|menu|label=Menu|lov={menu_lov}|on_action=menu_fct|>
"""

POPULAR_PRODUCTS_PAGE = """
# Predict Best **Products**{: .color-primary}

--------------------------------------------------------------------

## Filter by:<br/>
<|layout|columns=1 1 1 1|
Gender: <br/><|{selected_gender}|toggle|lov=Both;Male;Female|><br/>
Age: <br/><|{selected_ages}|slider|min=0|max=100|continuous=False|><br/>

Province: <br/><|{selected_province}|selector|dropdown|lov={provinces}|><br/>

Income (€): <br/><|{selected_incomes}|slider|min=0|max=1000000|continuous=False|><br/>

Seniority (months): <br/><|{selected_seniority}|slider|min=0|max=150|continuous=False|><br/>
|>

<|Filter|button|on_action=best_product|><br/>
<|Most Popular Products|expandable|expanded=False|
<|{product_counts}|chart|type=bar|title=Most Popular Products|>
|><br/>
<|Filtered list of clients|expandable|expanded|
<|{selected_data}|table|rebuild|filter|properties=style_properties|>
|>
<center><|Predict Best Products|button|on_action=product_prediction|><br/><br/></center>
<|Predicted Best Products|expandable|expanded={predictions_expand}|
<|{predicted_data}|table|rebuild|editable|filter|properties=style_properties|>
<|{predicted_counts_advertising}|chart|type=bar|title=Predicted Products|>
|>
<br/>
<center><|Launch Advertising Campaign|button|on_action=launch_campaign|><br/></center>
<br/>
<br/>
"""

ADVERTISING_RESULTS_PAGE = """
# Advertising **Results**{: .color-primary}

--------------------------------------------------------------------

<|{chosen_metric}|toggle|lov=Impressions;Click Rate; Buy Rate|on_change=update_metric|><br/>
<|{data_metric}|chart|type=line|rebuild|properties=properties_metric|><br/>
"""

CUSTOMER_DATA_PAGE = """
# Customer **Data**{: .color-primary}

--------------------------------------------------------------------


<|layout|columns=1 1|
<|{sex_chart_data}|chart|type=pie|values=Count|labels=Sex|title=Sex Distribution of Clients|><br/>
<|{age_chart_data}|chart|type=histogram|options={age_options}|title=Count by Age of Client|>

<|{province_chart_data}|chart|type=pie|values=Count|labels=Province|title=Province Distribution of Clients|><br/>
<|{income_chart_data}|chart|type=histogram|options={income_options}|title=Count by Income (€) of Client|>
|>
"""

pages = {
    "/": ROOT,
    "Popular-Products": POPULAR_PRODUCTS_PAGE,
    "Customer-Data": CUSTOMER_DATA_PAGE,
    "Advertising-Results": ADVERTISING_RESULTS_PAGE,
}

if __name__ == "__main__":
    gui = Gui(pages=pages)
    gui.run(
        title="Bank Product Recommender",
        dark_mode=False,
        debug=True,
        use_reloader=False,
    )
