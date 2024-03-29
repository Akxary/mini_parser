from matplotlib.ticker import MultipleLocator
from bs4 import BeautifulSoup as bs
from pathlib import Path
import pandas as pd
import re
import matplotlib.pyplot as plt
import requests
from datetime import datetime
import sys

src_file = Path("data_to_parse.html")
filt_list = ["Армения", "Германия", "Тбилиси", "США", "Франция"]
parse_url = "https://nadezhdin2024.ru/addresses"
headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.28 Safari/537.36"
}
max_per_region: int = 2_500
min_sum: int = 150_000


def update_input_data() -> tuple[str, str]:
    try:
        html_data = load_data()
        dttm = str(datetime.now().strftime(r"%Y-%m-%d %H:%M:%S"))
        save_data(html_data)
    except Exception as ex:
        print("HTTP ex occured: ", ex)
        html_data, dttm = read_data()
    return html_data, dttm


def load_data() -> str:
    session = requests.session()
    return session.get(parse_url, headers=headers).text


def save_data(inp: str, dttm: str = str(datetime.now().strftime(r"%Y-%m-%d %H:%M:%S"))):
    with open(src_file, encoding="utf-8", mode="w") as f:
        f.write(f"[time: {dttm}]" + "\n" + inp)


def read_data() -> tuple[str, str]:
    with open(src_file, encoding="utf-8") as f:
        read_strs = f.readlines()
        dttm = read_strs[0].removeprefix("[time: ").rstrip("]\n")
        return "".join(read_strs[1:]), dttm


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
    df["Зачтено"] = df["Число собранных"].apply(
        lambda x: x if x <= max_per_region else max_per_region
    )
    df["Число несобранных"] = df[["Число собранных", "out_flg"]].apply(
        lambda x: 0
        if (x["out_flg"] or (x["Число собранных"] >= max_per_region))
        else max_per_region - x["Число собранных"],
        axis=1,
    )
    return df[df["out_flg"] == False]


if __name__ == "__main__":
    flg: bool = False if sys.argv[1] == '0' else True
    if flg:
        html_data, dttm = update_input_data()
    else:
        html_data, dttm = read_data()

    df = find_all_data_by_region(html_data)
    df = df.set_index("Город")
    ax = df[["Число собранных", "Число несобранных"]].plot.bar(stacked=True)
    ax.yaxis.set_minor_locator(MultipleLocator(250))
    ax.grid(axis="y", which="both")
    fig = ax.get_figure()
    _fixed = df["Зачтено"].sum()
    if fig:
        fig.suptitle(
            "На {} всего собрано: {:_.0f}. Зачтено: {:_.0f}. Осталось собрать: {:_.0f}".format(
                dttm, df["Число собранных"].sum(), _fixed, min_sum - _fixed
            )
        )
    plt.tight_layout()
    plt.show()
