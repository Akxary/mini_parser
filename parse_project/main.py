from matplotlib.ticker import MultipleLocator
from bs4 import BeautifulSoup as bs
import os
from pathlib import Path
import pandas as pd
import re
import matplotlib.pyplot as plt
import requests
from datetime import time, datetime

src_file = Path("data_to_parse.html")
filt_list = ["Армения", "Германия", "Тбилиси", "США", "Франция"]
parse_url = "https://nadezhdin2024.ru/addresses"
headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.28 Safari/537.36"
}
max_per_region: int = 2_500


def load_data() -> str:
    session = requests.session()
    return session.get(parse_url, headers=headers).text


def find_all_data_by_region(in_data: str) -> pd.DataFrame:  # list[tuple[str, str]]
    bs_data = bs(in_data, "html.parser")
    pre_df_list: list[tuple[str, str, bool]] = []
    for el in bs_data.find_all("div", {"class": "addresses-page__region"}):
        name_el = (
            el.find("div", {"class": "card region-card region-card--addresses-page"})
            .find("h3", {"class": "subheading"})
            .text
        )
        stat_el = el.find("div", {"class": "progressbar addresses-page__progressbar"})
        if stat_el:
            out_flg = False
            stat_el = (
                stat_el.find("div", {"class": "progressbar__el"})
                .find("div", {"class": "progressbar__el__texts"})
                .find("span", {"class": "progressbar__el__text"})
                .text
            )
        else:
            out_flg = True
            stat_el = "-"
        pre_df_list.append((name_el, stat_el, out_flg))
    df = pd.DataFrame(
        pre_df_list,
        columns=["Город", "Собрано", "out_flg"],
    )
    df["Число собранных"] = df["Собрано"].apply(
        lambda x: int(re.findall(r"\d+", x)[0]) if re.findall(r"\d+", x) else 0
    )
    df["Число несобранных"] = df[["Число собранных", "out_flg"]].apply(
        lambda x: max_per_region - x["Число собранных"]
        if (x["Число собранных"] <= max_per_region or x["out_flg"])
        else 0,
        axis=1,
    )
    return df


if __name__ == "__main__":
    try:
        html_data = load_data()
        with open(src_file, encoding="utf-8", mode="w") as f:
            f.write(html_data)
        print("HTML file updated")
    except Exception as exp:
        print("Network exeption occured: ", exp)
        with open(src_file, encoding="utf-8") as f:
            html_data = "".join(f.readlines())

    df = find_all_data_by_region(html_data)
    df = df.set_index("Город")
    ax = df[["Число собранных", "Число несобранных"]].plot.bar(stacked=True)
    ax.yaxis.set_minor_locator(MultipleLocator(250))
    ax.grid(axis="y", which="both")
    fig = ax.get_figure()
    _time = datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")
    if fig:
        fig.suptitle(
            "На {} всего собрано: {:_.0f} / {:_.0f}".format(
                _time,
                df["Число собранных"].sum(),
                df.query("`out_flg`==False")["Число собранных"]
                .apply(lambda x: x if x <= max_per_region else max_per_region)
                .sum()
                + df["Число несобранных"].sum(),
            )
        )
    plt.tight_layout()
    plt.show()
