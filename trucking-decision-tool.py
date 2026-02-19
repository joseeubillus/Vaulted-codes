import streamlit as st
import pandas as pd


# Constants
diesel_combustion_emission_factor = 0.01303 #tCO2e/gal
cng_combustion_emission_factor = 0.0085 #tCO2e/gal
c_co2_ratio = 44/12 #gCO2/gC
lb_per_mwh_to_kg_per_kwh = 0.45359237/1000
energy_use_per_ton = 34.85 # kWh/metric ton

grid_emission_data_lb_per_mwh = {
    "ASCC Alaska": 905.109,
    "ASCC Miscellaneous": 522.400,
    "WECC Southwest": 706.189,
    "WECC California": 429.983,
    "ERCOT All": 736.629,
    "FRCC All": 784.785,
    "HICC Miscellaneous": 1133.294,
    "HICC Oahu": 1498.947,
    "MRO East": 1404.963,
    "MRO West": 926.552,
    "NPCC New England": 543.178,
    "WECC Northwest": 635.267,
    "NPCC NYC/Westchester": 865.744,
    "NPCC Long Island": 1189.333,
    "NPCC Upstate NY": 242.776,
    "Puerto Rico": 1548.530,
    "RFC East": 599.170,
    "RFC Michigan": 975.978,
    "RFC West": 916.054,
    "WECC Rockies": 1042.539,
    "SPP North": 867.740,
    "SPP South": 875.567,
    "SERC Mississippi Valley": 741.741,
    "SERC Midwest": 1248.582,
    "SERC South": 846.007,
    "SERC Tennessee Valley": 903.306,
    "SERC Virginia/Carolina": 596.326,
}

grid_loss = 0.04
# Page config
st.set_page_config(page_title="Waste Trucking Decision Tool", page_icon="🚚", layout="wide")

# Page title and description
st.title("Waste Trucking Decision Tool")
st.text("Trucking analysis from a unit economics perspective to evaluate secondary waste sources being trucked in to anchor/co-located sites")

#Input section
st.header("Input Parameters")
# Collapse some input under an expander
st.caption("Advanced trucking parameters include fuel efficiency, truck capacicty and fuel type. The default values are fuel efficiency = 6 mpg, truck capacity = 19 metric tons, and fuel type = diesel.")
with st.expander("Advanced Trucking Parameters"):
    st.caption("Enter the truck fuel efficiency in miles per gallon (mpg). The default value is 6 mpg, which is a common fuel efficiency for heavy-duty trucks.")
    truck_mpg = st.number_input('Truck fuel efficiency (mpg)', value=6.0)
    st.caption("Enter the truck capacity in metric tons. The default value is 19 metric tons, which is a common capacity for a standard semi-truck trailer.")
    truck_capacity_tons = st.number_input('Truck capacity (metric tons)', value=19.0)
    st.caption("Select the fuel type used for trucking. The default value is diesel, which is commonly used for heavy-duty trucks. If CNG is selected, the tool will use the corresponding emission factor for calculations.")
    fuel_type = st.selectbox('Truck fuel type', ['Diesel', 'CNG'])
    if fuel_type == 'Diesel':
        emission_factor = diesel_combustion_emission_factor
    else:
        emission_factor = cng_combustion_emission_factor

st.subheader("Operational variables")
st.caption('Choose the range for the waste stream TOC (%) as received')
toc = st.slider('TOC of waste as received in percent (%)',min_value=4.0,max_value=60.0, value=(4.0, 8.0), step=2.0)
# Generate toc values for the selected range with step 2
toc_values = list(range(int(toc[0]), int(toc[1]) + 2, 2))
st.caption("Choose the driving distance range from source to site in miles. If waste is sourced on-site, enter 0.")
distance_to_waste = st.slider('Distance to waste (miles)',min_value=0.0,max_value=500.0, value=(0.0, 100.0), step=5.0)
distance_values = list(range(int(distance_to_waste[0]), int(distance_to_waste[1]) + 1, 5))

st.caption("Select the grid region that best represents the electricity used at the site. If you have a custom grid emission factor, select 'Custom' and enter the value in kgCO2e/kWh.")
selected_grid = st.selectbox('Grid region', list(grid_emission_data_lb_per_mwh.keys()))
selected_grid_lb_per_mwh = grid_emission_data_lb_per_mwh[selected_grid]
selected_grid_kg_per_kwh = selected_grid_lb_per_mwh * lb_per_mwh_to_kg_per_kwh

emission_input_mode = st.selectbox('Emission factor input', ['Use 2023 EGrid data', 'Custom'])
if emission_input_mode == 'Use 2023 EGrid data':
    grid_emission_factor = selected_grid_kg_per_kwh
else:
    grid_emission_factor = st.number_input('Custom grid emission factor (kgCO2e/kWh)', min_value=0.0, value=float(selected_grid_kg_per_kwh))

st.caption(f"Selected grid emission: {selected_grid_lb_per_mwh:.3f} lb/MWh = {selected_grid_kg_per_kwh:.3f} kgCO2e/kWh")
st.subheader("Revenue and cost variables")
col5, col6, col7 = st.columns(3)
with col5:
    st.caption('Enter the most appropiate CRU Revenue per ton.')
    cru_revenue_per_ton = st.number_input('CRU Revenue ($/CRU)', value=250.0)
with col6:
    st.caption("Enter the transportation cost per mile in dollars.")
    transport_cost_per_mile = st.number_input('Transportation cost per mile ($/mile)', min_value=0.0, value=3.5)
with col7:
    st.caption("Enter the operational expenses (OPEX) in dollars per metric ton.")
    opex_cost = st.number_input('Operational expenses (OPEX) ($/ton)', min_value=1.0, value=6.3)

st.caption("Select the tipping fee in dollars per metric ton. The default value is $50/ton, which is a common tipping fee for waste disposal.")
tipping_fee = st.slider('Tipping fee ($/ton)', min_value=-10.0,max_value=150.0, value=50.0, step=5.0)
# Calculations
st.header("Decision metrics")
st.caption("All other emissions are considered negligible for this analysis, including upstream fuel production and vehicle manufacturing emissions. The tool focuses on direct combustion emissions from trucking, which are the most significant contributors to the carbon footprint of waste transportation.")
# 1. Calculate the CO2e stored per ton of waste based on TOC content
gross_co2e_per_ton = [toc_value / 100 * c_co2_ratio for toc_value in toc_values]
# 2. Calculate transport emissions per ton of waste using the distance_to_waste, truck_mpg, truck_capacity_tons, and the selected fuel's emission factor
transport_emissions_per_ton = [emission_factor*(2*distance/truck_mpg) * (1/truck_capacity_tons) for distance in distance_values]
# 3. Calculate energy emissions per ton of waste using the selected grid emission factor, energy use per ton, and grid losses
loss_multiplier = 1 + grid_loss
adjusted_grid_emission_factor = grid_emission_factor * loss_multiplier
energy_emissions = energy_use_per_ton * adjusted_grid_emission_factor/1000 # convert kgCO2e to tCO2e
# 4. Calculate the net CO2e stored per ton of waste after accounting for transport emissions each gross CO2e to each transport emission values
# Store in a dataframe where the first column is distance and each column after that is the net CO2e for each TOC value
net_co2e_data = {'Distance (miles)': distance_values}
for i, toc_value in enumerate(toc_values):
    net_co2e_data[f'TOC {toc_value}%'] = [gross_co2e_per_ton[i] - transport_emissions - energy_emissions for transport_emissions in transport_emissions_per_ton]
net_co2e_df = pd.DataFrame(net_co2e_data)

# 5. Calculate the profit per ton of waste based on tipping fee, transport cost, and opex cost
# Profit is equal to the cru_revenue * net_co2e minus the tipping fee, transport cost, and opex cost
# Store in a dataframe where the first column is distance and each column after that is the profit for each TOC value
profit_data = {'Distance (miles)': distance_values}
for i, toc_value in enumerate(toc_values):
    profit_data[f'TOC {toc_value}%'] = [cru_revenue_per_ton * net_co2e + tipping_fee -  transport_cost_per_mile * 2 * distance/truck_capacity_tons - opex_cost for net_co2e, distance in zip(net_co2e_data[f'TOC {toc_value}%'], distance_values)]
profit_df = pd.DataFrame(profit_data)

# Display two columns, table to the left and plot to the right
st.subheader("Waste:CRU Ratio vs distance")
col1, col2 = st.columns(2)
with col1:
    st.dataframe(net_co2e_df)
with col2:
    st.line_chart(net_co2e_df.set_index('Distance (miles)'),
                  x_label='Distance to waste (miles)', 
                  y_label='Waste:CRU Ratio')

st.subheader("Profit vs distance")
col3, col4 = st.columns(2)
with col3:
    st.dataframe(profit_df)
with col4:
    st.line_chart(profit_df.set_index('Distance (miles)'),
                  x_label='Distance to waste (miles)', 
                  y_label='Profit ($/ton)',
                  use_container_width=True)






