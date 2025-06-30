# ===================== UltimateChart V2.1.0 (Calculation-Only Version) =======================
# Version: 2.1.0
# Last Updated: 2025-06-28
# Description: This version is stripped down to focus exclusively on trade planning
#              and calculation. All Google Sheets connectivity, portfolio management,
#              AI assistant, and data logging have been removed. The initial balance
#              is now set manually by the user in the sidebar.
# ==============================================================================================

# ============== 1. IMPORTS ==============
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ============== 2. PAGE CONFIGURATION ==============
st.set_page_config(page_title="Trade Planner", layout="wide")

st.title("เครื่องมือวางแผนการเทรด (Trade Planner)")
st.markdown("กรอกข้อมูลใน Sidebar ด้านซ้ายเพื่อคำนวณแผนการเทรดของคุณ")

# ============== 3. SESSION STATE INITIALIZATION (Simplified) ==============
# --- Trade Planning Inputs ---
if "asset_fibo" not in st.session_state: st.session_state.asset_fibo = "XAUUSD"
if "risk_pct_fibo" not in st.session_state: st.session_state.risk_pct_fibo = 1.0
if "direction_fibo" not in st.session_state: st.session_state.direction_fibo = "Long"
if "swing_high_fibo" not in st.session_state: st.session_state.swing_high_fibo = ""
if "swing_low_fibo" not in st.session_state: st.session_state.swing_low_fibo = ""
if "fibo_flags" not in st.session_state: st.session_state.fibo_flags = [True] * 5
if "asset_fibo_multiplier" not in st.session_state: st.session_state.asset_fibo_multiplier = 100.0 # New multiplier for XAUUSD

if "asset_custom" not in st.session_state: st.session_state.asset_custom = "XAUUSD"
if "risk_pct_custom" not in st.session_state: st.session_state.risk_pct_custom = 1.0
if "n_entry_custom" not in st.session_state: st.session_state.n_entry_custom = 2
if "asset_custom_multiplier" not in st.session_state: st.session_state.asset_custom_multiplier = 100.0 # New multiplier for XAUUSD
# เพิ่มตัวแปรสำหรับ Lot Display Multiplier ใน session_state
if "display_lot_multiplier" not in st.session_state: st.session_state.display_lot_multiplier = 1.0 # ค่าเริ่มต้นเป็น 1 (แสดงเป็น Standard Lot)

for i in range(st.session_state.get("n_entry_custom", 2)):
    if f"custom_entry_{i}" not in st.session_state: st.session_state[f"custom_entry_{i}"] = "0.00"
    if f"custom_sl_{i}" not in st.session_state: st.session_state[f"custom_sl_{i}"] = "0.00"
    if f"custom_tp_{i}" not in st.session_state: st.session_state[f"custom_tp_{i}"] = "0.00"

# ============== 4. SIDEBAR - USER INPUTS ==============
st.sidebar.header("⚙️ ตั้งค่าการคำนวณ")

# --- Manual Balance Input ---
account_balance = st.sidebar.number_input(
    "💰 บาลานซ์เริ่มต้น (Account Balance)",
    min_value=0.01,
    value=st.session_state.get("account_balance", 10000.0),
    step=1000.0,
    format="%.2f",
    key="account_balance",
    help="ใส่ยอดเงินในพอร์ตของคุณเพื่อใช้ในการคำนวณความเสี่ยงและขนาด Lot"
)

# --- Trade Mode Selection ---
mode = st.sidebar.radio("เลือกโหมดการเทรด", ["FIBO", "CUSTOM"], horizontal=True, key="trade_mode")
st.sidebar.markdown("---")

# --- ตัวคูณ Lot สำหรับการแสดงผล (NEW INPUT) ---
st.session_state.display_lot_multiplier = st.sidebar.number_input(
    "ตัวคูณ Lot สำหรับการแสดงผล (Lot Display Multiplier)",
    min_value=0.01,
    value=st.session_state.display_lot_multiplier,
    step=1.0,
    format="%.2f",
    help="""
    หากโบรกเกอร์ของคุณแสดง 0.01 Lot Standard เป็น '1' หน่วย (Micro Lot)
    ให้ป้อน 100.00 ที่นี่ (Lot ที่คำนวณได้จะถูกคูณด้วย 100 เพื่อแสดงผล)
    หากโบรกเกอร์แสดงเป็น 0.01, 0.1, 1.0 ตามปกติ ให้ป้อน 1.00
    """
)
st.sidebar.markdown("---")

# --- Input Forms based on Mode ---
if mode == "FIBO":
    st.sidebar.subheader("คำนวณจาก Fibo")
    col1, col2, col3 = st.sidebar.columns([2, 2, 2])
    st.session_state.asset_fibo = col1.text_input("ชื่อสินทรัพย์", value=st.session_state.asset_fibo)
    st.session_state.risk_pct_fibo = col2.number_input("Risk %", min_value=0.01, value=st.session_state.risk_pct_fibo, step=0.1, format="%.2f")
    st.session_state.direction_fibo = col3.radio("ทิศทาง", ["Long", "Short"], index=["Long", "Short"].index(st.session_state.direction_fibo), horizontal=True)

    col4, col5 = st.sidebar.columns(2)
    st.session_state.swing_high_fibo = col4.text_input("Swing High", value=st.session_state.swing_high_fibo)
    st.session_state.swing_low_fibo = col5.text_input("Swing Low", value=st.session_state.swing_low_fibo)

    # Multiplier input for FIBO mode
    st.session_state.asset_fibo_multiplier = st.sidebar.number_input(
        "มูลค่า 1 USD Price Move ต่อ 1 Lot Standard (เช่น 100 สำหรับ XAUUSD)",
        min_value=0.01,
        value=st.session_state.asset_fibo_multiplier,
        step=1.0,
        format="%.2f",
        help="สำหรับ XAUUSD (ทองคำ), โดยทั่วไปคือ 100 (เพราะ 1 Lot Standard = 100 ออนซ์, 1 USD price move = 100 USD risk)"
    )

    st.sidebar.markdown("**ระดับ Fibo ที่ต้องการเข้าเทรด**")
    fibo_options = [0.114, 0.25, 0.382, 0.5, 0.618]
    cols_cb = st.sidebar.columns(len(fibo_options))
    for i, col in enumerate(cols_cb):
        st.session_state.fibo_flags[i] = col.checkbox(f"{fibo_options[i]:.2f}", value=st.session_state.fibo_flags[i], key=f"fibo_cb_{i}")

elif mode == "CUSTOM":
    st.sidebar.subheader("กำหนดค่าเอง (Custom)")
    col1, col2 = st.sidebar.columns(2)
    st.session_state.asset_custom = col1.text_input("ชื่อสินทรัพย์", value=st.session_state.asset_custom)
    st.session_state.risk_pct_custom = col2.number_input("Risk % (รวมทุกไม้)", min_value=0.01, value=st.session_state.risk_pct_custom, step=0.1, format="%.2f")
    st.session_state.n_entry_custom = st.sidebar.number_input("จำนวนไม้", min_value=1, max_value=10, value=st.session_state.n_entry_custom, step=1)

    # Multiplier input for CUSTOM mode
    st.session_state.asset_custom_multiplier = st.sidebar.number_input(
        "มูลค่า 1 USD Price Move ต่อ 1 Lot Standard (เช่น 100 สำหรับ XAUUSD)",
        min_value=0.01,
        value=st.session_state.asset_custom_multiplier,
        step=1.0,
        format="%.2f",
        help="สำหรับ XAUUSD (ทองคำ), โดยทั่วไปคือ 100 (เพราะ 1 Lot Standard = 100 ออนซ์, 1 USD price move = 100 USD risk)"
    )

    for i in range(st.session_state.n_entry_custom):
        st.sidebar.markdown(f"--- ไม้ที่ {i+1} ---")
        c1, c2, c3 = st.sidebar.columns(3)
        st.session_state[f"custom_entry_{i}"] = c1.text_input(f"Entry {i+1}", value=st.session_state.get(f"custom_entry_{i}", "0.00"), key=f"cust_e_{i}")
        st.session_state[f"custom_sl_{i}"] = c2.text_input(f"SL {i+1}", value=st.session_state.get(f"custom_sl_{i}", "0.00"), key=f"cust_sl_{i}")
        st.session_state[f"custom_tp_{i}"] = c3.text_input(f"TP {i+1}", value=st.session_state.get(f"custom_tp_{i}", "0.00"), key=f"cust_tp_{i}")

# ============== 5. CALCULATION ENGINE & STRATEGY SUMMARY ==============
st.sidebar.markdown("---")
st.sidebar.subheader("🧾 สรุปแผน (Strategy Summary)")

# Initialize summary variables
total_lots = 0.0
total_risk_dollar = 0.0
avg_rr = 0.0
total_profit_at_tp = 0.0
calculated_plan_data = [] # This list will hold dicts for each entry to display in the main table

# Constants for Fibo TP calculations
RATIO_TP1_EFF = 1.618
RATIO_TP2_EFF = 2.618
RATIO_TP3_EFF = 4.236

# --- FIBO Mode Calculation ---
if mode == "FIBO":
    try:
        high_str = st.session_state.swing_high_fibo
        low_str = st.session_state.swing_low_fibo
        risk_pct = st.session_state.risk_pct_fibo
        direction = st.session_state.direction_fibo
        flags = st.session_state.fibo_flags
        num_selected_entries = sum(flags)
        # Get multiplier for lot calculation
        asset_multiplier = st.session_state.asset_fibo_multiplier
        display_lot_multiplier_val = st.session_state.display_lot_multiplier # ดึงค่าตัวคูณสำหรับการแสดงผล

        if not high_str or not low_str or num_selected_entries == 0:
            st.sidebar.info("กรอก High/Low และเลือก Fibo Level เพื่อคำนวณ")
        else:
            high = float(high_str)
            low = float(low_str)
            if high <= low:
                st.sidebar.warning("High ต้องมากกว่า Low")
            else:
                trade_range = high - low
                total_risk_allowed = account_balance * (risk_pct / 100.0)
                risk_per_entry = total_risk_allowed / num_selected_entries
                rr_list = []

                for i, is_selected in enumerate(flags):
                    if is_selected:
                        fibo_ratio = fibo_options[i]
                        entry, sl, tp1 = 0.0, 0.0, 0.0

                        if direction == "Long":
                            entry = low + (trade_range * fibo_ratio)
                            sl = low
                            tp1 = low + (trade_range * RATIO_TP1_EFF)
                        else: # Short
                            entry = high - (trade_range * fibo_ratio)
                            sl = high
                            tp1 = high - (trade_range * RATIO_TP1_EFF)

                        stop_dist_usd = abs(entry - sl) # ระยะห่าง Stop Loss เป็นหน่วย USD Price Move
                        
                        lot, risk, rr, profit = 0.0, 0.0, 0.0, 0.0
                        if stop_dist_usd > 1e-9 and asset_multiplier > 0: # ตรวจสอบ asset_multiplier ด้วย
                            # คำนวณ Lot ใหม่: Risk($) / (Stop Loss Distance(USD) * มูลค่า 1 USD Price Move ต่อ 1 Lot Standard)
                            lot = risk_per_entry / (stop_dist_usd * asset_multiplier)
                            
                            # เตรียม Lot สำหรับการแสดงผล (ใช้ตัวคูณ Lot Display)
                            display_lot = lot * display_lot_multiplier_val

                            risk = lot * stop_dist_usd * asset_multiplier # Risk คำนวณตาม Lot ที่ได้
                            target_dist_usd = abs(tp1 - entry)
                            
                            # ตรวจสอบทิศทางของ TP เพื่อคำนวณ RR และ Profit ที่มีกำไรเท่านั้น
                            is_long = direction == "Long"
                            is_tp_profitable = (is_long and tp1 > entry) or (not is_long and tp1 < entry)

                            if is_tp_profitable:
                                rr = target_dist_usd / stop_dist_usd
                                profit = lot * target_dist_usd * asset_multiplier
                                rr_list.append(rr)
                            else:
                                rr = 0.0 # ถ้า TP ไม่ทำกำไร RR เป็น 0
                                profit = 0.0

                        total_lots += lot # total_lots ยังคงเป็น Standard Lot
                        total_risk_dollar += risk
                        total_profit_at_tp += profit
                        calculated_plan_data.append({
                            "Fibo Level": f"{fibo_ratio:.2f}", "Entry": entry, "SL": sl, "TP (Global TP1)": tp1,
                            "Lot": display_lot, # ใช้ display_lot ในการแสดงผล
                            "Risk $": risk, "RR": rr
                        })
                if rr_list:
                    avg_rr = np.mean(rr_list)

    except (ValueError, ZeroDivisionError) as e:
        st.sidebar.error(f"ข้อมูลไม่ถูกต้อง: {e}")
    except Exception as e:
        st.sidebar.error(f"เกิดข้อผิดพลาด: {e}")

# --- CUSTOM Mode Calculation ---
elif mode == "CUSTOM":
    try:
        num_entries = st.session_state.n_entry_custom
        risk_pct = st.session_state.risk_pct_custom
        total_risk_allowed = account_balance * (risk_pct / 100.0)
        risk_per_entry = total_risk_allowed / num_entries if num_entries > 0 else 0
        rr_list = []
        # Get multiplier for lot calculation
        asset_multiplier = st.session_state.asset_custom_multiplier
        display_lot_multiplier_val = st.session_state.display_lot_multiplier # ดึงค่าตัวคูณสำหรับการแสดงผล

        for i in range(num_entries):
            entry_str = st.session_state[f"custom_entry_{i}"]
            sl_str = st.session_state[f"custom_sl_{i}"]
            tp_str = st.session_state[f"custom_tp_{i}"]
            
            entry, sl, tp = float(entry_str), float(sl_str), float(tp_str)
            stop_dist_usd = abs(entry - sl) # ระยะห่าง Stop Loss เป็นหน่วย USD Price Move
            
            lot, risk, rr, profit = 0.0, 0.0, 0.0, 0.0
            if stop_dist_usd > 1e-9 and asset_multiplier > 0: # ตรวจสอบ asset_multiplier ด้วย
                # คำนวณ Lot ใหม่: Risk($) / (Stop Loss Distance(USD) * มูลค่า 1 USD Price Move ต่อ 1 Lot Standard)
                lot = risk_per_entry / (stop_dist_usd * asset_multiplier)
                
                # เตรียม Lot สำหรับการแสดงผล (ใช้ตัวคูณ Lot Display)
                display_lot = lot * display_lot_multiplier_val

                risk = lot * stop_dist_usd * asset_multiplier # Risk คำนวณตาม Lot ที่ได้
                target_dist_usd = abs(tp - entry)
                
                # Check for profitable direction before calculating RR
                is_long = entry > sl # กำหนดทิศทางจาก Entry > SL (Long) หรือ Entry < SL (Short)
                is_tp_profitable = (is_long and tp > entry) or (not is_long and tp < entry)
                
                if is_tp_profitable:
                    rr = target_dist_usd / stop_dist_usd
                    profit = lot * target_dist_usd * asset_multiplier
                    rr_list.append(rr)
                else:
                    rr = 0.0 # ถ้า TP ไม่ทำกำไร RR เป็น 0
                    profit = 0.0

            total_lots += lot # total_lots ยังคงเป็น Standard Lot
            total_risk_dollar += risk
            total_profit_at_tp += profit
            calculated_plan_data.append({
                "ไม้ที่": i + 1, "Entry": entry, "SL": sl, "TP": tp,
                "Lot": display_lot, # ใช้ display_lot ในการแสดงผล
                "Risk $": risk, "RR": rr
            })
        if rr_list:
            avg_rr = np.mean(rr_list)

    except (ValueError, ZeroDivisionError) as e:
        st.sidebar.error(f"ข้อมูลไม่ถูกต้อง: {e}")
    except Exception as e:
        st.sidebar.error(f"เกิดข้อผิดพลาด: {e}")

# --- Display Summary in Sidebar ---
if total_risk_dollar > 0:
    # แสดง Total Lots เป็น Standard Lot (ไม่ได้คูณด้วย display_lot_multiplier)
    st.sidebar.write(f"**Total Lots (Standard Lot):** {total_lots:.2f}")
    st.sidebar.write(f"**Total Risk $ (คำนวณ):** {total_risk_dollar:.2f}")
    st.sidebar.write(f"**Average RR:** {avg_rr:.2f}")
    st.sidebar.write(f"**Total Expected Profit:** {total_profit_at_tp:,.2f} USD")

# ============== 6. MAIN AREA - RESULTS DISPLAY ==============
with st.expander("📋 ตารางแผนการเทรด (Entry Table)", expanded=True):
    if not calculated_plan_data:
        st.info("ผลการคำนวณจะแสดงที่นี่หลังจากกรอกข้อมูลใน Sidebar ครบถ้วน")
    else:
        df_plan = pd.DataFrame(calculated_plan_data)
        
        # --- Format DataFrame for display ---
        format_mapping = {}
        for col in ["Entry", "SL", "TP", "TP (Global TP1)"]:
            if col in df_plan.columns:
                format_mapping[col] = "{:,.5f}"
        for col in ["Lot", "Risk $", "RR"]:
            if col in df_plan.columns:
                format_mapping[col] = "{:,.2f}"

        st.dataframe(df_plan.style.format(format_mapping), use_container_width=True, hide_index=True)

        # --- Display Fibo Global TPs if applicable ---
        if mode == "FIBO":
            try:
                high, low = float(st.session_state.swing_high_fibo), float(st.session_state.swing_low_fibo)
                direction = st.session_state.direction_fibo
                if high > low:
                    trade_range = high - low
                    st.markdown("### 🎯 Global Take Profit Zones (FIBO)")
                    
                    if direction == "Long":
                        tp1 = low + (trade_range * RATIO_TP1_EFF)
                        tp2 = low + (trade_range * RATIO_TP2_EFF)
                        tp3 = low + (trade_range * RATIO_TP3_EFF)
                    else:
                        tp1 = high - (trade_range * RATIO_TP1_EFF)
                        tp2 = high - (trade_range * RATIO_TP2_EFF)
                        tp3 = high - (trade_range * RATIO_TP3_EFF)

                    tp_df = pd.DataFrame({
                        "TP Zone": [f"TP1 ({RATIO_TP1_EFF:.2f})", f"TP2 ({RATIO_TP2_EFF:.2f})", f"TP3 ({RATIO_TP3_EFF:.2f})"],
                        "Price": [f"{tp1:.5f}", f"{tp2:.5f}", f"{tp3:.5f}"]
                    })
                    st.dataframe(tp_df, hide_index=True, use_container_width=True)
            except (ValueError, TypeError):
                 pass # Don't show error if inputs are not valid numbers yet
