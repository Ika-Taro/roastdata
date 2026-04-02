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
    "SOAK1_M", "SOAK1_S", "SOAK1_H", "SOAK1_A",
    "SOAK2_M", "SOAK2_S", "SOAK2_H", "SOAK2_A",
    "TP_M", "TP_S", "TP_TEMP",
    "MAILLARD_M", "MAILLARD_S", "MAILLARD_TEMP", "MAILLARD_H", "MAILLARD_A",
    "T190_M", "T190_S", "T190_H", "T190_A",
    "CRACK1_M", "CRACK1_S", "CRACK1_TEMP",
    "T190P1_M", "T190P1_S", "T190P1_H", "T190P1_A",
    "HAS_CRACK2", "CRACK2_M", "CRACK2_S",
    "DISCHARGE_M", "DISCHARGE_S", "DISCHARGE_TEMP",
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
    "SOAK1_M": 0, "SOAK1_S": 30, "SOAK1_H": 40, "SOAK1_A": 1.0,
    "SOAK2_M": 1, "SOAK2_S": 0, "SOAK2_H": 40, "SOAK2_A": 2.0,
    "TP_M": 2, "TP_S": 0, "TP_TEMP": 110,
    "MAILLARD_M": 5, "MAILLARD_S": 0, "MAILLARD_TEMP": 150, "MAILLARD_H": 60, "MAILLARD_A": 3.5,
    "T190_M": 8, "T190_S": 0, "T190_H": 60, "T190_A": 4.5,
    "CRACK1_M": 8, "CRACK1_S": 40, "CRACK1_TEMP": 195,
    "T190P1_M": 9, "T190P1_S": 0, "T190P1_H": 50, "T190P1_A": 3.0,
    "HAS_CRACK2": True,
    "CRACK2_M": 12, "CRACK2_S": 0,
    "DISCHARGE_M": 12, "DISCHARGE_S": 30, "DISCHARGE_TEMP": 230,
    "MEMO": ""
}

for key, val in default_values.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==========================================
# 3. UIコンポーネント用関数
# ==========================================
def event_row(label, prefix, has_temp=False, has_control=True, time_disabled=False):
    st.markdown(f"**{label}**")
    cols = st.columns([1.5, 1.5, 1.5, 2, 2])
    with cols[0]:
        st.number_input("分", min_value=0, max_value=59, key=f"{prefix}_M", step=1, disabled=time_disabled)
    with cols[1]:
        st.number_input("秒", min_value=0, max_value=59, key=f"{prefix}_S", step=1, disabled=time_disabled)
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

def safe_get(row, key, default=""):
    val = row.get(key)
    return val if pd.notna(val) else default

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
                    if key in row_data and pd.notna(row_data[key]):
                        st.session_state[key] = row_data[key]
                        
                # 古いデータの互換性処理（自動マッピング）
                if "SOAK_M" in row_data and pd.notna(row_data["SOAK_M"]):
                    st.session_state["SOAK2_M"] = row_data["SOAK_M"]
                    st.session_state["SOAK2_S"] = row_data["SOAK_S"]
                if "T150_M" in row_data and pd.notna(row_data["T150_M"]):
                    st.session_state["MAILLARD_M"] = row_data["T150_M"]
                    st.session_state["MAILLARD_S"] = row_data["T150_S"]
                    st.session_state["MAILLARD_H"] = row_data.get("T150_H", 0)
                    st.session_state["MAILLARD_A"] = row_data.get("T150_A", 0)
                    st.session_state["MAILLARD_TEMP"] = 150
                if "T195_M" in row_data and pd.notna(row_data["T195_M"]):
                    st.session_state["T190_M"] = row_data["T195_M"]
                    st.session_state["T190_S"] = row_data["T195_S"]
                    st.session_state["T190_H"] = row_data.get("T195_H", 0)
                    st.session_state["T190_A"] = row_data.get("T195_A", 0)
                if "T195P1_M" in row_data and pd.notna(row_data["T195P1_M"]):
                    st.session_state["T190P1_H"] = row_data.get("T195P1_H", 0)
                    st.session_state["T190P1_A"] = row_data.get("T195P1_A", 0)

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
        event_row("ソーキング", "SOAK1", has_temp=False, has_control=True)
        event_row("ソーキング終了", "SOAK2", has_temp=False, has_control=True)
        event_row("中点 (TP)", "TP", has_temp=True, has_control=False)
        event_row("メイラード開始", "MAILLARD", has_temp=True, has_control=True)
        event_row("190℃ 到達", "T190", has_temp=False, has_control=True)
        event_row("1ハゼ", "CRACK1", has_temp=True, has_control=False)
        
        # 190℃ + 1min の自動計算
        t190_sec = get_sec("T190")
        t190p1_sec = t190_sec + 60
        st.session_state["T190P1_M"] = t190p1_sec // 60
        st.session_state["T190P1_S"] = t190p1_sec % 60
        event_row("190℃ + 1min", "T190P1", has_temp=False, has_control=True, time_disabled=True)
        
        # 2ハゼ（チェックボックス連動）
        st.markdown("---")
        no_crack2 = st.checkbox("2ハゼなし（到達しない）", value=not st.session_state["HAS_CRACK2"])
        st.session_state["HAS_CRACK2"] = not no_crack2
        if not no_crack2:
            event_row("2ハゼ", "CRACK2", has_temp=False, has_control=False)
        
        event_row("排出 (DISCHARGE)", "DISCHARGE", has_temp=True, has_control=False)

    st.header("3. プロファイル分析 & 保存")
    t_maillard_sec = get_sec("MAILLARD")
    t_crack_sec = get_sec("CRACK1")
    t_end_sec = get_sec("DISCHARGE")
    
    total_sec = t_end_sec if t_end_sec > 0 else 1
    dry_pct = (t_maillard_sec / total_sec) * 100 if t_maillard_sec > 0 else 0
    maillard_sec = t_crack_sec - t_maillard_sec
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
        display_cols = ["プロファイル名", "ORIGIN", "ROAST_LEVEL", "CHARGE_TEMP", "LOSS_PCT", "DRY_PCT", "MAILLARD_PCT", "DEV_PCT"]
        display_df = df_logs[[c for c in display_cols if c in df_logs.columns]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab3:
    st.header("AI焙煎師への評価依頼用データ")
    st.write("プロファイルを選択すると、テキストが生成されます。コピーしてチャットに貼り付けてください。")
    
    eval_recipe = st.selectbox("出力するプロファイルを選択", [""] + df_logs["プロファイル名"].tolist(), key="eval_select")
    
    if eval_recipe != "":
        row = df_logs[df_logs["プロファイル名"] == eval_recipe].iloc[0]
        
        crack2_text = ""
        if safe_get(row, 'HAS_CRACK2', True):
            crack2_text = f"・2ハゼ: {int(safe_get(row, 'CRACK2_M', 0)):02d}:{int(safe_get(row, 'CRACK2_S', 0)):02d}\n"
        
        report_text = f"""【焙煎記録プロフェッショナルレポート】
プロファイル名: {safe_get(row, 'プロファイル名')}
ORIGIN: {safe_get(row, 'ORIGIN')}
PROCESS: {safe_get(row, 'PROCESS')}
ROAST_LEVEL: {safe_get(row, 'ROAST_LEVEL')}
ROOM_TEMP: {safe_get(row, 'ROOM_TEMP')}℃
BATCH_SIZE: {safe_get(row, 'BATCH_SIZE')}g
ROASTED_WEIGHT: {safe_get(row, 'ROASTED_WEIGHT')}g
LOSS_PCT: {safe_get(row, 'LOSS_PCT')}%
CHARGE_TEMP: {safe_get(row, 'CHARGE_TEMP')}℃

[TIMELINE / DTR]
DRY: {safe_get(row, 'DRY_PCT')}%
MAILLARD: {safe_get(row, 'MAILLARD_PCT')}%
DEV (DTR): {safe_get(row, 'DEV_PCT')}%

[OPERATION LOG]
・ソーキング: {int(safe_get(row, 'SOAK1_M', 0)):02d}:{int(safe_get(row, 'SOAK1_S', 0)):02d} | Heat: {safe_get(row, 'SOAK1_H', '-')} | Air: {safe_get(row, 'SOAK1_A', '-')}
・ソーキング終了: {int(safe_get(row, 'SOAK2_M', 0)):02d}:{int(safe_get(row, 'SOAK2_S', 0)):02d} | Heat: {safe_get(row, 'SOAK2_H', '-')} | Air: {safe_get(row, 'SOAK2_A', '-')}
・中点(TP): {int(safe_get(row, 'TP_M', 0)):02d}:{int(safe_get(row, 'TP_S', 0)):02d} @ {safe_get(row, 'TP_TEMP', '-')}℃
・メイラード開始: {int(safe_get(row, 'MAILLARD_M', 0)):02d}:{int(safe_get(row, 'MAILLARD_S', 0)):02d} @ {safe_get(row, 'MAILLARD_TEMP', '-')}℃ | Heat: {safe_get(row, 'MAILLARD_H', '-')} | Air: {safe_get(row, 'MAILLARD_A', '-')}
・190℃到達: {int(safe_get(row, 'T190_M', 0)):02d}:{int(safe_get(row, 'T190_S', 0)):02d} | Heat: {safe_get(row, 'T190_H', '-')} | Air: {safe_get(row, 'T190_A', '-')}
・1ハゼ: {int(safe_get(row, 'CRACK1_M', 0)):02d}:{int(safe_get(row, 'CRACK1_S', 0)):02d} @ {safe_get(row, 'CRACK1_TEMP', '-')}℃
・190℃+1min: {int(safe_get(row, 'T190P1_M', 0)):02d}:{int(safe_get(row, 'T190P1_S', 0)):02d} | Heat: {safe_get(row, 'T190P1_H', '-')} | Air: {safe_get(row, 'T190P1_A', '-')}
{crack2_text}・排出: {int(safe_get(row, 'DISCHARGE_M', 0)):02d}:{int(safe_get(row, 'DISCHARGE_S', 0)):02d} @ {safe_get(row, 'DISCHARGE_TEMP', '-')}℃

MEMO: {safe_get(row, 'MEMO')}
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