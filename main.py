"""Entry point for the bank recommender application"""

import pandas as pd
from taipy.gui import Gui, State, Icon, notify, navigate

DATA_PATH = "data/customer_data.csv"

customer_data = pd.read_csv(DATA_PATH)

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

customer_data[product_columns] = customer_data[product_columns].astype(bool)
selected_data = customer_data.copy()


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


page = "Popular Products"

menu_lov = [
    ("Popular Products", Icon("images/popular_products.png", "Popular Products")),
    ("Customer Data", Icon("images/customer_data.png", "Customer Data")),
]

ROOT = """
<|menu|label=Menu|lov={menu_lov}|on_action=menu_fct|>
"""

POPULAR_PRODUCTS_PAGE = """
# Popular **Products**{: .color-primary}

--------------------------------------------------------------------

## Filter by:<br/>
<|layout|columns=1 1 1 1|
Gender: <br/><|{selected_gender}|toggle|lov=Both;Male;Female|on_change=best_product|><br/>

Age: <br/><|{selected_ages}|slider|min=0|max=100|on_change=best_product|continuous=False|><br/>

Province: <br/><|{selected_province}|selector|dropdown|lov={provinces}|on_change=best_product|><br/>

Income (€): <br/><|{selected_incomes}|slider|min=0|max=1000000|on_change=best_product|continuous=False|><br/>
|>

<|{product_counts}|chart|type=bar|title=Most Popular Products|><br/>
<|Filtered list of clients|expandable|expanded|
<|{selected_data}|table|rebuild|>
|>
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
}

if __name__ == "__main__":
    gui = Gui(pages=pages)
    gui.run(
        title="Bank Product Recommender", dark_mode=False, debug=True, use_reloader=True
    )
