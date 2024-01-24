from datetime import datetime
import streamlit as st
import plotly.express as px
from copy import deepcopy
import pandas as pd

# to use dashboard: streamlit run .\parse_project\dashboard.py

# import seaborn as sns
from main_funcs import (
    find_all_data_by_region,
    update_input_data,
    min_sum,
)




if __name__ == "__main__":
    def button_callback():
        global df, dttm
        sub_str, dttm = update_input_data()
        df = find_all_data_by_region(sub_str)
    
    sub_str, dttm = update_input_data()
    df = find_all_data_by_region(sub_str)
    df = df.set_index("Город")
    df["grp"] = df["Число собранных"].apply(
        lambda x: ">=2500"
        if x >= 2500
        else "1000-2500"
        if 1000 <= x < 2500
        else "500-1000"
        if 500 <= x < 1000
        else "0-500"
    )
    st.title("Данные по сбору")
    _list_to_select = df["grp"].drop_duplicates().to_numpy()
    selection = st.multiselect(
        "Число подписей",
        _list_to_select,
        default=_list_to_select,
    )
    # st.select_slider('abc', options=df.index.to_numpy())
    if selection:
        df_f = df.query(f"`grp`.isin({selection})")
    else:
        df_f = deepcopy(df)
    input_towns = st.multiselect("Поиск городов", df_f.index)
    if input_towns:
        df_f = df_f.loc[list(filter(lambda x: x in input_towns, df.index))]

    fig = px.histogram(
        df_f[["Число собранных", "Число несобранных"]],
        x=df_f.index,
        y=["Число собранных", "Число несобранных"],
        labels={"x": "Город"},
    )
    fig.update_layout(yaxis_title="Число подписей", yaxis_range=[0, 3500])
    _fixed = df["Зачтено"].sum()
    st.text(
        "На {}\nВсего собрано: {:_.0f}\nЗачтено: {:_.0f}\nОсталось собрать: {:_.0f}".format(
            dttm,
            df["Число собранных"].sum(),
            _fixed,
            min_sum - _fixed,
        ).replace(
            "_", " "
        )
    )
    st.button('Обновить данные', on_click=button_callback)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_f[filter(lambda x: x not in ("out_flg", "grp"), df.columns)])
