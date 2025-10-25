import pandas as pd
import streamlit as st
import plotly.graph_objs as go


def load_data():
    consumption_df = pd.read_csv(r"Data\Electricity_consumption_2015-2025.csv")
    consumption_df['time'] = pd.to_datetime(consumption_df['time'], format='%Y-%m-%d %H:%M:%S')
    price_df = pd.read_csv(r"Data\Electricity_price_2015-2025.csv", delimiter=";", decimal=',')
    price_df['timestamp'] = pd.to_datetime(price_df['timestamp'], format='%H:%M %m/%d/%Y')

    expense_df = pd.merge(price_df, consumption_df, left_on='timestamp', right_on='time', how='inner')
    expense_df.drop('time', axis='columns', inplace=True)
    expense_df["hourly_expense"] = (expense_df["kWh"] * expense_df["Price"]) / 100.0
    return expense_df


def aggregate(df, freq):
    agg = df.resample(freq, on="timestamp", label="left", closed="left").agg({
        "kWh": "sum",
        "Price": "mean",
        "hourly_expense": "sum",
        "Temperature": "mean",
    })
    agg = agg.reset_index()
    agg["fixed_cost_eur"] = 0.0
    agg["cost_total_eur"] = agg["hourly_expense"]

    return agg


df = load_data()

st.set_page_config(page_title="Electricity Analytics", page_icon="⚡", layout="wide")
st.title("Electricity Usage & Price Dashboard")

start_date = st.date_input("Start time", df["timestamp"].dt.date.min())
end_date = st.date_input("End time", df["timestamp"].dt.date.max())
mask_date = (df["timestamp"].dt.date >= start_date) & (df["timestamp"].dt.date <= end_date)
view = df.loc[mask_date].copy()

st.write(f"Showing range: ", start_date, " - ", end_date)
st.write(f"Total consumption over the period: ", view['kWh'].sum().round(1), " kWh")
st.write("Total bill over the period: ", view['hourly_expense'].sum().round(2), " €")
st.write(f"Average hourly price: ", (view['Price'].sum() / len(view)).round(2), " cents")
st.write(f"Average paid price: ", (view['hourly_expense'].sum() / view['kWh'].sum() * 100.0).round(2), " cents")
st.write(f"Average temperature: ", (view['Temperature'].sum() / len(view)).round(2), " °C")

freq = st.selectbox("Averaging period:", ["Daily", "Weekly", "Monthly"], index=1)

# Aggregation
freq_map = {
    "Daily": "D",
    "Weekly": "W-MON",
    "Monthly": "MS",
}

ag = aggregate(view, freq_map[freq])

graph_height = 550
consumption_fig = go.Figure()
consumption_fig.add_trace(go.Scatter(x=ag["timestamp"], y=ag["kWh"], name="Electricity consumption [kWh]", mode="lines"))
consumption_fig.update_layout(
    title="Usage Over Time",
    xaxis_title="Time",
    yaxis_title="Electricity consumption [kWh]",
    height=graph_height
)
st.plotly_chart(consumption_fig, use_container_width=True)

price_fig = go.Figure()
price_fig.add_trace(go.Scatter(x=ag["timestamp"], y=ag["Price"], name="Electricity price [cents]", mode="lines"))
price_fig.update_layout(
    title="Price Over Time",
    xaxis_title="Time",
    yaxis_title="Electricity price [cents]",
    height=graph_height
)
st.plotly_chart(price_fig, use_container_width=True)

bill_fig = go.Figure()
bill_fig.add_trace(go.Scatter(x=ag["timestamp"], y=ag["hourly_expense"], name="Electricity bill [€]", mode="lines"))
bill_fig.update_layout(
    title="Cost Over Time",
    xaxis_title="Time",
    yaxis_title="Electricity bill [€]",
    height=graph_height
)
st.plotly_chart(bill_fig, use_container_width=True)

temperature_fig = go.Figure()
temperature_fig.add_trace(go.Scatter(x=ag["timestamp"], y=ag["Temperature"], name="Temperature (C)", mode="lines"))
temperature_fig.update_layout(
    title="Temperature",
    xaxis_title="Time",
    yaxis_title="Temperature",
    height=graph_height
)
st.plotly_chart(temperature_fig, use_container_width=True)
