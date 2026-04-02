import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="焙煎記録アプリ", layout="wide")
st.title("☕ ROASTING LOG & RECIPE")

# ==========================================
# 1. データベース接続と初期化
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)
sheet_name = "RoastLogs"

COLUMNS = [
    "プロファイル名", "日付", "ORIGIN", "PROCESS", "ROAST_LEVEL", "ROOM_TEMP", "CHARGE_TEMP", 
    "BATCH_SIZE", "ROASTED_WEIGHT", "LOSS_PCT",
    "SOAK_M", "SOAK_S", "SOAK_H", "SOAK_A",
    "TP_M", "TP_S", "TP_TEMP", "TP_H", "TP_A",
    "T150_M", "T150_S", "T150_H", "T150_A",
    "T195_M", "T195_S", "T195_H", "T195_A",
    "CRACK1_M", "CRACK1_S", "CRACK1_TEMP",
    "T195P1_M", "T195P1_S", "T195P1_H", "T195P1_A",
    "CRACK2_M", "CRACK2_S",
    "DISCHARGE_M", "DISCHARGE_S", "DISCHARGE_TEMP", "DISCHARGE_H", "DISCHARGE_A",
    "DRY_PCT", "MAILLARD_PCT", "DEV_PCT", "MEMO"
]

try:
    df_logs = conn.read(worksheet=sheet_name, ttl="10m")
    if df_logs.empty or "プロファイル名" not in df_logs.columns:
        df_logs = pd.DataFrame(columns=COLUMNS)
    df_logs = df_logs.dropna(subset=["プロファイル名"])
except Exception:
    df_logs = pd.DataFrame(columns=COLUMNS)

# ==========================================
# 2. セッションステート初期化
# ==========================================
default_values = {
    "ORIGIN": "Brazil", "PROCESS": "Natural", "ROAST_LEVEL": "深煎", 
    "ROOM_TEMP": 20.0, "CHARGE_TEMP": 200, "BATCH_SIZE": 700, "ROASTED_WEIGHT": 0,
    "SOAK_M": 1, "SOAK_S": 0, "SOAK_H": 40, "SOAK_A": 2.0,
    "TP_M": 2, "TP_S": 0, "TP_TEMP": 110, "TP_H": 100, "TP_A": 3.5,
    "T150_M": 5, "T150_S": 0, "T150_H": 60, "T150_A": 3.5,
    "T195_M": 8, "T195_S": 30, "T195_H": 60, "T195_A": 4.5,
    "CRACK1_M": 8, "CRACK1_S": 40, "CRACK1_TEMP": 195,
    "T195P1_M": 9, "T195P1_S": 40, "T195P1_H": 50, "T195P1_A": 3.0,
    "CRACK2_M": 12, "CRACK2_S": 0,
    "DISCHARGE_M": 12, "DISCHARGE_S": 30, "DISCHARGE_TEMP": 230, "DISCHARGE_H": 0, "DISCHARGE_A": 8.0,
    "MEMO": ""
}

for key, val in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==========================================
# 3. UIコンポーネント用関数
# ==========================================
def event_row(label, prefix, has_temp=False, has_control=True):
    st.markdown(f"**{label}**")
    cols = st.columns([1.5, 1.5, 1.5, 2, 2])
    with cols[0]:
        st.number_input("分", min_value=0, max_value=59, key=f"{prefix}_M", step=1)
    with cols[1]:
        st.number_input("秒", min_value=0, max_value=59, key=f"{prefix}_S", step=1)
    with cols[2]:
        if has_temp:
            st.number_input("温度(℃)", key=f"{prefix}_TEMP", step=1)
    with cols[3]:
        if has_control:
            st.slider("Heat(火力)", 0, 100, key=f"{prefix}_H", step=5)
    with cols[4]:
        if has_control:
            st.slider("Air(排気)", 0.0, 8.0, key=f"{prefix}_A", step=0.5)
    st.markdown("---")

def get_sec(prefix):
    return st.session_state[f"{prefix}_M"] * 60 + st.session_state[f"{prefix}_S"]

# ==========================================
# 4. メイン画面レイアウト
# ==========================================
tab1, tab2, tab3 = st.tabs(["🔥 焙煎の記録・実行", "📂 過去レシピの管理・読込", "📤 AI評価用出力・CSV出力"])

with tab1:
    st.success("💡 **過去のレシピを呼び出す**")
    col_load1, col_load2 = st.columns([3, 1])
    with col_load1:
        recipe_list = ["（新規・または現在の設定のまま）"] + df_logs["プロファイル名"].tolist()
        selected_recipe = st.selectbox("ベースにするプロファイルを選択", recipe_list)
    with col_load2:
        st.write("") 
        if st.button("設定を読み込む", use_container_width=True):
            if selected_recipe != "（新規・または現在の設定のまま）":
                row_data = df_logs[df_logs["プロファイル名"] == selected_recipe].iloc[0]
                for key in default_values.keys():
                    if key in row_data:
                        st.session_state[key] = row_data[key]
                st.rerun()

    st.header("1. 基本情報")
    b_col1, b_col2, b_col3, b_col4 = st.columns(4)
    with b_col1:
        st.text_input("ORIGIN (産地)", key="ORIGIN")
        st.number_input("ROOM TEMP (室温)", key="ROOM_TEMP", step=0.5)
    with b_col2:
        st.selectbox("PROCESS (精製)", ["Washed", "Natural", "Honey", "Anaerobic", "Others"], key="PROCESS")
        st.number_input("CHARGE (投入温度)", key="CHARGE_TEMP", step=1)
    with b_col3:
        st.selectbox("ROAST LEVEL", ["浅煎", "中煎", "中深煎", "深煎"], key="ROAST_LEVEL")
        st.number_input("BATCH SIZE (投入量 g)", key="BATCH_SIZE", step=10)
    with b_col4:
        st.write("") 
        st.number_input("ROASTED (焙煎後重量 g)", key="ROASTED_WEIGHT", step=1)
        batch = st.session_state["BATCH_SIZE"]
        roasted = st.session_state["ROASTED_WEIGHT"]
        loss_pct = ((batch - roasted) / batch * 100) if batch > 0 and roasted > 0 else 0
        st.metric("LOSS (目減り率)", f"{loss_pct:.1f}%")

    st.header("2. タイムライン & 操作ログ")
    with st.container():
        event_row("ソーキング終了", "SOAK", has_temp=False, has_control=True)
        event_row("中点 (TP)", "TP", has_temp=True, has_control=True)
        event_row("150℃ 到達", "T150", has_temp=False, has_control=True)
        event_row("195℃ 到達", "T195", has_temp=False, has_control=True)
        event_row("1ハゼ", "CRACK1", has_temp=True, has_control=False)
        event_row("195℃ + 1min", "T195P1", has_temp=False, has_control=True)
        event_row("2ハゼ (※到達した場合)", "CRACK2", has_temp=False, has_control=False)
        event_row("排出 (DISCHARGE)", "DISCHARGE", has_temp=True, has_control=True)

    st.header("3. プロファイル分析 & 保存")
    t_150_sec = get_sec("T150")
    t_crack_sec = get_sec("CRACK1")
    t_end_sec = get_sec("DISCHARGE")
    
    total_sec = t_end_sec if t_end_sec > 0 else 1
    dry_pct = (t_150_sec / total_sec) * 100 if t_150_sec > 0 else 0
    maillard_sec = t_crack_sec - t_150_sec
    maillard_pct = (maillard_sec / total_sec) * 100 if maillard_sec > 0 else 0
    dev_sec = t_end_sec - t_crack_sec
    dev_pct = (dev_sec / total_sec) * 100 if dev_sec > 0 else 0

    a_col1, a_col2, a_col3, a_col4 = st.columns(4)
    a_col1.metric("TOTAL TIME", f"{int(t_end_sec//60):02d}:{int(t_end_sec%60):02d}")
    a_col2.metric("DRY (%)", f"{dry_pct:.1f}%")
    a_col3.metric("MAILLARD (%)", f"{maillard_pct:.1f}%")
    a_col4.metric("DEV/DTR (%)", f"{dev_pct:.1f}%")

    st.text_area("MEMO (特記事項・カッピング評価など)", key="MEMO")

    if st.button("💾 この焙煎記録をスプレッドシートに保存する", use_container_width=True):
        today_str = datetime.now().strftime("%Y/%m/%d")
        profile_name = f"[{today_str}] {st.session_state['ORIGIN']} ({st.session_state['ROAST_LEVEL']})"
        save_data = {"プロファイル名": profile_name, "日付": today_str, "LOSS_PCT": round(loss_pct, 1), 
                     "DRY_PCT": round(dry_pct, 1), "MAILLARD_PCT": round(maillard_pct, 1), "DEV_PCT": round(dev_pct, 1)}
        for key in default_values.keys():
            save_data[key] = st.session_state[key]
            
        new_df = pd.DataFrame([save_data])
        updated_df = pd.concat([df_logs, new_df], ignore_index=True)
        try:
            conn.update(worksheet=sheet_name, data=updated_df)
            st.cache_data.clear()
            st.success(f"「{profile_name}」を保存しました！")
        except Exception as e:
            st.error(f"保存エラー: {e}")

with tab2:
    st.header("保存済みのプロファイル一覧")
    if df_logs.empty:
        st.info("データがありません。")
    else:
        display_df = df_logs[["プロファイル名", "ORIGIN", "ROAST_LEVEL", "CHARGE_TEMP", "LOSS_PCT", "DRY_PCT", "MAILLARD_PCT", "DEV_PCT"]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab3:
    st.header("AI焙煎師への評価依頼用データ")
    st.write("プロファイルを選択すると、AIが読み取りやすいフォーマットでテキストが生成されます。右上のコピーアイコンからコピーしてチャットに貼り付けてください。")
    
    eval_recipe = st.selectbox("出力するプロファイルを選択", [""] + df_logs["プロファイル名"].tolist(), key="eval_select")
    
    if eval_recipe != "":
        row = df_logs[df_logs["プロファイル名"] == eval_recipe].iloc[0]
        report_text = f"""【焙煎記録プロフェッショナルレポート】
プロファイル名: {row['プロファイル名']}
ORIGIN: {row['ORIGIN']}
PROCESS: {row['PROCESS']}
ROAST_LEVEL: {row['ROAST_LEVEL']}
ROOM_TEMP: {row['ROOM_TEMP']}℃
BATCH_SIZE: {row['BATCH_SIZE']}g
ROASTED_WEIGHT: {row['ROASTED_WEIGHT']}g
LOSS_PCT: {row['LOSS_PCT']}%
CHARGE_TEMP: {row['CHARGE_TEMP']}℃

[TIMELINE / DTR]
DRY: {row['DRY_PCT']}%
MAILLARD: {row['MAILLARD_PCT']}%
DEV (DTR): {row['DEV_PCT']}%

[OPERATION LOG]
・ソーキング終了: {int(row['SOAK_M']):02d}:{int(row['SOAK_S']):02d} | Heat: {row['SOAK_H']} | Air: {row['SOAK_A']}
・中点(TP): {int(row['TP_M']):02d}:{int(row['TP_S']):02d} @ {row['TP_TEMP']}℃ | Heat: {row['TP_H']} | Air: {row['TP_A']}
・150℃到達: {int(row['T150_M']):02d}:{int(row['T150_S']):02d} | Heat: {row['T150_H']} | Air: {row['T150_A']}
・195℃到達: {int(row['T195_M']):02d}:{int(row['T195_S']):02d} | Heat: {row['T195_H']} | Air: {row['T195_A']}
・1ハゼ: {int(row['CRACK1_M']):02d}:{int(row['CRACK1_S']):02d} @ {row['CRACK1_TEMP']}℃
・195℃+1min: {int(row['T195P1_M']):02d}:{int(row['T195P1_S']):02d} | Heat: {row['T195P1_H']} | Air: {row['T195P1_A']}
・2ハゼ: {int(row['CRACK2_M']):02d}:{int(row['CRACK2_S']):02d}
・排出: {int(row['DISCHARGE_M']):02d}:{int(row['DISCHARGE_S']):02d} @ {row['DISCHARGE_TEMP']}℃ | Heat: {row['DISCHARGE_H']} | Air: {row['DISCHARGE_A']}

MEMO: {row['MEMO']}
"""
        st.code(report_text, language="markdown")

    st.markdown("---")
    st.header("全データのCSVエクスポート")
    if not df_logs.empty:
        csv = df_logs.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 全焙煎ログをCSVでダウンロード",
            data=csv,
            file_name=f"roast_logs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )