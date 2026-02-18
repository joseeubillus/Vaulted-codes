import streamlit as st

# Constants
diesel_combustion_emission_factor = 0.01303 #tCO2e/gal
c_co2_ratio = 44/12 #gCO2/gC
truck_mpg = 6 # miles per gallon
truck_capacity_tons = 19 # metric tons
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


# Configure the streamlit app
st.set_page_config(page_title="LCA Calculator", page_icon="🌿", layout="centered"
                   )
# Title and description
st.title("Simplified Life Cycle Assessment for Site Selection")
st.caption("This tool calculates the waste:CRU ratio and CDR efficiency" \
"based on TOC content, distance to source, grid electricity, counterfactual storage, and replacement emissions.")
# Describe the underlying assumptions
st.subheader("Assumptions")
st.caption(
    f"Fixed assumptions: diesel EF={diesel_combustion_emission_factor:.5f} tCO2e/gal,"
    f"truck efficiency={truck_mpg} mpg, truck capacity={truck_capacity_tons} metric tons,"
    f"C→CO2 ratio={c_co2_ratio:.3f}, energy use={energy_use_per_ton:.2f} kWh/metric ton, "
    f"grid energy losses={grid_loss*100:.1f}%."
)

# Input sections
st.subheader("Input Parameters")
st.caption("Enter the most appropiate TOC (%) as received for the site waste stream")
toc = st.number_input('TOC of waste as received in percent (%)',min_value=4.0)
st.caption("If waste is trucked to the site, enter the distance from source to site. If waste is sourced on-site, enter 0.")
distance_to_waste = st.number_input('Distance to waste (miles)',min_value=0.0)
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

st.caption("Enter the most appropiate percentage of counterfactual storage. Consult CDR team on best value based on waste ")
counterfactual_storage_percentage = st.number_input('Counterfactual storage percentage (%)', min_value=0.0)

# 1. Calculate the gross CO2e
gross_co2e = toc/100 * c_co2_ratio
# 2. Calculate transport emissions
transport_emissions = diesel_combustion_emission_factor*(distance_to_waste/truck_mpg) * (1/truck_capacity_tons)
# 3. Calculate energy emissions
loss_multiplier = 1 + grid_loss
adjusted_grid_emission_factor = grid_emission_factor * loss_multiplier
energy_emissions = energy_use_per_ton * adjusted_grid_emission_factor/1000 # convert kgCO2e to tCO2e
# 4. Counterfactual and replacement emissions
replacement_emissions = st.number_input('Replacement emissions (tCO2e/metric ton)', min_value=0.0)
counterfactual_emissions = (counterfactual_storage_percentage/100) * gross_co2e
# 6. Total emissions
total_emissions = transport_emissions + energy_emissions + replacement_emissions + counterfactual_emissions
# 7. Calculate net tons of CO2e
net_co2e = gross_co2e - total_emissions
# CDR Efficiency
cdr_efficiency = (net_co2e / gross_co2e) * 100
# Display results in a table format
st.subheader("Life Cycle Assessment per ton of waste")
st.write(f"**Gross CO2e Stored per ton of waste:** {gross_co2e:.3f} tCO2e/metric ton")
st.write(f"**Transportation Emissions per ton of waste:** {transport_emissions:.3f} tCO2e/metric ton")
st.write(f"**Energy Emissions per ton of waste:** {energy_emissions:.3f} tCO2e/metric ton")
st.write(f"**Counterfactual Emissions per ton of waste:** {counterfactual_emissions:.3f} tCO2e/metric ton")
st.write(f"**Replacement Emissions per ton of waste:** {replacement_emissions:.3f} tCO2e/metric ton")
st.write(f"**Total Emissions per ton of waste:** {total_emissions:.3f} tCO2e/metric ton")
st.subheader('Site Performance Indicators')
st.write(f"**Waste:CRU Ratio:** {net_co2e:.3f} tCO2e/metric ton")
st.write(f"**CDR Efficiency:** {cdr_efficiency:.2f} %")

