from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
# to use dashboard: streamlit run .\parse_project\dashboard.py

# import seaborn as sns
from main import (
    find_all_data_by_region,
    src_file,
    load_data,
    save_data,
    read_data,
    min_sum,
)


if __name__ == "__main__":
    try:
        html_data = load_data()
        save_data(html_data)
    except Exception as ex:
        print("HTTP ex occured: ", ex)
        html_data = read_data()

    # df = sns.load_dataset('titanic')
    df = find_all_data_by_region(html_data)
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
    df_f = df.query(f"`grp`.isin({selection})")
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
            datetime.now().strftime(r"%Y-%m-%d %H:%M:%S"),
            df["Число собранных"].sum(),
            _fixed,
            min_sum - _fixed,
        ).replace(
            "_", " "
        )
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(df_f[filter(lambda x: x not in ("out_flg", "grp"), df.columns)])
