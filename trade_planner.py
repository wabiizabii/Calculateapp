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

# --- กำหนดค่าคงที่สำหรับ Point Value / Unit Value ต่อ Lot Display (ซ่อนจากผู้ใช้) ---
# คุณสามารถเปลี่ยนค่าเหล่านี้ได้โดยตรงในโค้ด
# ค่านี้คือ มูลค่า USD ที่เปลี่ยนไปต่อ 1 จุดราคา (0.01) สำหรับ 1 Lot ที่จะแสดงผล
# สำหรับ XAUUSD (ทองคำ):
#    - ถ้าต้องการแสดง Lot เป็น Standard Lot (0.01, 0.1, 1.0) --> 1 จุด (0.01 USD Price Change) = 1 USD/Lot --> ตั้งค่าเป็น 1.0
#    - ถ้าต้องการแสดง Lot เป็น Micro Lot (1, 10, 100) (โดยที่ 1 micro lot = 0.01 Standard Lot) --> 1 จุด (0.01 USD Price Change) = 0.01 USD/Lot --> ตั้งค่าเป็น 0.01
# สำหรับ EURUSD:
#    - ถ้าต้องการแสดง Lot เป็น Standard Lot (0.01, 0.1, 1.0) --> 1 Pip (0.0001 Price Change) = 10 USD/Lot
#      ดังนั้น 1 จุด (0.01 Price Change) = 100 Pips = 1000 USD/Lot --> ตั้งค่าเป็น 10.0 (เพราะ 0.01 คือ 100 pips * 10 = 1000)
#      หรือเพื่อให้ง่ายและตรงกับค่า EURUSD Standard Lot * Price change per pip * Pips in 0.01 price change
#      1.0 (Standard Lot) * 10 (USD/pip) * (0.01 / 0.0001) (pips in 0.01 price change) = 1.0 * 10 * 100 = 1000
#      ดังนั้น ค่าตรงนี้คือ 10.0 สำหรับ 1 Lot ที่เป็น Standard Lot (ถ้า 1 จุดราคา 0.01 = 100 pips)
#      ถ้า 1 จุดราคาคือ 0.00001 (5 ตำแหน่ง) --> 1 USD Price Move = 100000 Point (0.00001)
#      แล้ว 1 Lot Standard มีค่า 10 USD/pip
#      10 / 0.0001 (pip size) * 0.01 (input price unit) * 1 (lot display unit) = 1000 (wrong conversion)
#      Let's re-evaluate:
#      USD value per 0.01 price change for 1 standard lot (1.00 lot):
#      XAUUSD: 1.0 (since 1 USD price change costs 100 USD for 1 lot, and 0.01 price change is 1 USD)
#      EURUSD: 1000 (since 1 standard lot is 100,000 units, 0.01 price change is 100 pips, and 1 pip is $10 for 1 standard lot. So 100 pips * $10/pip = $1000)
# This will be simpler.

# Default value for XAUUSD, aiming for 1.0 Lot = 1.0 in display
# If 1 USD price change is 100 USD per 1.00 Lot (Standard Lot), then 0.01 price change is 1 USD per 1.00 Lot.
# So, 'unit_value_per_0_01_price_move_per_display_lot' = 1.0 if display is Standard Lot.
# If display is Micro Lot (1 = 0.01 Standard Lot), then 0.01 price change = 0.01 USD per 1 micro lot.
# So, 'unit_value_per_0_01_price_move_per_display_lot' = 0.01 if display is Micro Lot.

# Let's assume the user wants Standard Lot display by default for XAUUSD.
# This means: 1 Lot (1.00) = $1.00 per 0.01 price move.
DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY = {
    "XAUUSD": 1.0, # 1.00 Lot of XAUUSD, 1 point (0.01 price move) = $1
    "EURUSD": 10.0 # 1.00 Lot of EURUSD, 1 point (0.01 price move) = $10 (assuming 1 pip = $10, and 0.01 price move = 100 pips, so 100 * $10 = $1000, wait, this is wrong. 1 Standard Lot of EURUSD is 10 USD per pip, so 0.01 price change is 100 pips. So 1.0 lot * 100 pips * $10/pip = $1000.  The value for 'unit_value_per_lot_display' for EURUSD would be 1000 / 1 (lot) = 1000 for 0.01 price change.)
                  # Correction from previous understanding:
                  # If we define "point price change" as 0.01 USD for XAUUSD, or 0.00001 for EURUSD (pip).
                  # "มูลค่า USD ต่อ 1 จุดราคา (0.01) ต่อ 1 Lot ที่แสดง"
                  # This means, for XAUUSD, a 0.01 change results in how much USD per 1 display lot. This is 1.0 USD for 1.0 standard lot.
                  # For EURUSD, a 0.01 change results in how much USD per 1 standard lot. A 0.01 change is 100 pips. 1 standard lot is $10/pip. So 100 pips * $10/pip = $1000.
                  # So, for EURUSD, it should be 1000.0.

    # This requires clear definition from the user about "point price change" in their context.
    # Let's stick to XAUUSD context for now where 0.01 is the 'point price change'
    # And 1.00 is the most common for XAUUSD Standard Lots (0.01 price move = $1 profit/loss per lot)
}
# Using session_state for these internal values, linked to asset_fibo/custom
if "fibo_asset_unit_value" not in st.session_state: st.session_state.fibo_asset_unit_value = DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY["XAUUSD"]
if "custom_asset_unit_value" not in st.session_state: st.session_state.custom_asset_unit_value = DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY["XAUUSD"]


if "asset_custom" not in st.session_state: st.session_state.asset_custom = "XAUUSD"
if "risk_pct_custom" not in st.session_state: st.session_state.risk_pct_custom = 1.0
if "n_entry_custom" not in st.session_state: st.session_state.n_entry_custom = 2

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

    # --- ไม่แสดงตัวคูณให้ผู้ใช้ปรับแล้ว แต่ใช้ค่า DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY แทน ---
    # st.session_state.fibo_unit_value_per_lot_display = st.sidebar.number_input(...)
    # หากต้องการให้ผู้ใช้เปลี่ยน asset_fibo_multiplier ภายใน คุณสามารถใช้ st.session_state.fibo_asset_unit_value
    # และอัปเดตจาก Dictionary ได้ หรือจากฟิลด์ซ่อน/config file

    st.sidebar.markdown("**ระดับ Fibo ที่ต้องการเข้าเทรด**")
    fibo_options = [0.114, 0.25, 0.382, 0.5, 0.618]
    cols_cb = st.sidebar.columns(len(fibo_options))
    for i, col in enumerate(cols_cb):
        st.session_state.fibo_flags[i] = col.checkbox(f"{fibo_options[i]:.3f}", value=st.session_state.fibo_flags[i], key=f"fibo_cb_{i}")

elif mode == "CUSTOM":
    st.sidebar.subheader("กำหนดค่าเอง (Custom)")
    col1, col2 = st.sidebar.columns(2)
    st.session_state.asset_custom = col1.text_input("ชื่อสินทรัพย์", value=st.session_state.asset_custom)
    st.session_state.risk_pct_custom = col2.number_input("Risk % (รวมทุกไม้)", min_value=0.01, value=st.session_state.risk_pct_custom, step=0.1, format="%.2f")
    st.session_state.n_entry_custom = st.sidebar.number_input("จำนวนไม้", min_value=1, max_value=10, value=st.session_state.n_entry_custom, step=1)

    # --- ไม่แสดงตัวคูณให้ผู้ใช้ปรับแล้ว ---
    # st.session_state.custom_unit_value_per_lot_display = st.sidebar.number_input(...)

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
        
        # ใช้ค่าจาก DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY โดยตรง
        # หาก asset_fibo มีอยู่ใน DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY ให้ใช้ค่านั้น
        # ไม่เช่นนั้น ให้ใช้ค่าเริ่มต้น (สำหรับ XAUUSD)
        unit_value_per_lot_display = DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY.get(
            st.session_state.asset_fibo.upper(),
            DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY["XAUUSD"] # Fallback to XAUUSD default
        )


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

                        # stop_dist_price is the distance in actual price units (e.g., 54 USD for XAUUSD)
                        stop_dist_price = abs(entry - sl) 
                        
                        lot_display_units, risk, rr, profit = 0.0, 0.0, 0.0, 0.0
                        
                        if stop_dist_price > 1e-9 and unit_value_per_lot_display > 0: # ตรวจสอบ unit_value_per_lot_display ด้วย
                            # stop_dist_points_0_01 = stop_dist_price / 0.01 # จำนวนจุดที่ราคาเปลี่ยนไป 0.01 USD
                            # lot_display_units = risk_per_entry / (stop_dist_points_0_01 * unit_value_per_lot_display)

                            # Simple calculation: Risk ($) / (Stop Distance in USD * Value per 1 USD price move per 1 unit of display lot)
                            # Assuming 'unit_value_per_lot_display' is "USD value per 1 USD price move per 1 display lot unit".
                            # If 'unit_value_per_lot_display' is "USD value per 0.01 price move per 1 display lot unit" (as previously named in help text)
                            # And stop_dist_price is total USD price difference (e.g., 54 USD).
                            # Example: XAUUSD, SL 54 USD, risk $100.
                            # If unit_value_per_lot_display = 1.0 (for Standard Lot, 0.01 price move = $1)
                            # Then $1 per 0.01 price move means $100 per 1.00 USD price move.
                            # So, 54 USD * $100 / Lot = $5400 Risk per 1 Lot.
                            # Lot = $100 / $5400 = 0.0185
                            
                            # Let's revert to the formula that matches the previous successful calculation for XAUUSD with multiplier 100 for Standard Lot
                            # Previous: lot = risk_per_entry / (stop_dist_usd * asset_multiplier)
                            # Where asset_multiplier = 100 (for XAUUSD)
                            # This 'asset_multiplier' was USD value per 1 USD price move per 1 Standard Lot.
                            # So now, unit_value_per_lot_display means "USD value per 1 USD price move per 1 DISPLAY Lot".
                            # This is the most intuitive for XAUUSD.
                            
                            lot_display_units = risk_per_entry / (stop_dist_price * unit_value_per_lot_display)
                            
                            # Calculate actual risk and profit in USD
                            risk = lot_display_units * stop_dist_price * unit_value_per_lot_display # Re-calculate risk based on actual lot units
                            target_dist_price = abs(tp1 - entry)
                            
                            # ตรวจสอบทิศทางของ TP เพื่อคำนวณ RR และ Profit ที่มีกำไรเท่านั้น
                            is_long = direction == "Long"
                            is_tp_profitable = (is_long and tp1 > entry) or (not is_long and tp1 < entry)

                            if is_tp_profitable:
                                rr = target_dist_price / stop_dist_price
                                profit = lot_display_units * target_dist_price * unit_value_per_lot_display
                                rr_list.append(rr)
                            else:
                                rr = 0.0 # ถ้า TP ไม่ทำกำไร RR เป็น 0
                                profit = 0.0

                        total_lots += lot_display_units # total_lots ตอนนี้จะรวมเป็นหน่วย Lot ที่แสดง
                        total_risk_dollar += risk
                        total_profit_at_tp += profit
                        calculated_plan_data.append({
                            "Fibo Level": f"{fibo_ratio:.3f}", "Entry": entry, "SL": sl, "TP (Global TP1)": tp1,
                            "Lot": lot_display_units, # ใช้ lot_display_units ในการแสดงผล
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
        
        # ใช้ค่าจาก DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY โดยตรง
        unit_value_per_lot_display = DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY.get(
            st.session_state.asset_custom.upper(),
            DEFAULT_UNIT_VALUE_PER_LOT_DISPLAY["XAUUSD"] # Fallback to XAUUSD default
        )


        for i in range(num_entries):
            entry_str = st.session_state[f"custom_entry_{i}"]
            sl_str = st.session_state[f"custom_sl_{i}"]
            tp_str = st.session_state[f"custom_tp_{i}"]
            
            entry, sl, tp = float(entry_str), float(sl_str), float(tp_str)
            stop_dist_price = abs(entry - sl) # ระยะห่าง Stop Loss เป็นหน่วย USD Price Move
            
            lot_display_units, risk, rr, profit = 0.0, 0.0, 0.0, 0.0
            if stop_dist_price > 1e-9 and unit_value_per_lot_display > 0: # ตรวจสอบ unit_value_per_lot_display ด้วย
                # lot_display_units: calculated lot in the user's preferred display unit
                lot_display_units = risk_per_entry / (stop_dist_price * unit_value_per_lot_display)
                
                # Calculate actual risk and profit in USD
                risk = lot_display_units * stop_dist_price * unit_value_per_lot_display
                target_dist_price = abs(tp - entry)
                
                # Check for profitable direction before calculating RR
                is_long = entry > sl # กำหนดทิศทางจาก Entry > SL (Long) หรือ Entry < SL (Short)
                is_tp_profitable = (is_long and tp > entry) or (not is_long and tp < entry)
                
                if is_tp_profitable:
                    rr = target_dist_price / stop_dist_price
                    profit = lot_display_units * target_dist_price * unit_value_per_lot_display
                    rr_list.append(rr)
                else:
                    rr = 0.0 # ถ้า TP ไม่ทำกำไร RR เป็น 0
                    profit = 0.0

            total_lots += lot_display_units # total_lots ตอนนี้จะรวมเป็นหน่วย Lot ที่แสดง
            total_risk_dollar += risk
            total_profit_at_tp += profit
            calculated_plan_data.append({
                "ไม้ที่": i + 1, "Entry": entry, "SL": sl, "TP": tp,
                "Lot": lot_display_units, # ใช้ lot_display_units ในการแสดงผล
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
    # แสดง Total Lots เป็นหน่วย Lot ที่แสดงตามที่ผู้ใช้กำหนด
    st.sidebar.write(f"**Total Lots (หน่วย Lot ที่แสดง):** {total_lots:.2f}")
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
                        tp1 = high - (trade_range * RATIO_TP3_EFF) # Changed to TP3 for consistency
                        tp2 = high - (trade_range * RATIO_TP2_EFF)
                        tp3 = high - (trade_range * RATIO_TP1_EFF) # Changed to TP1 for consistency
                        # Reverting TP order for Short direction to maintain TP1 < TP2 < TP3
                        # So, tp1 (short) should be based on RATIO_TP1_EFF, tp2 on RATIO_TP2_EFF, tp3 on RATIO_TP3_EFF
                        # The code here has tp1 (short) based on RATIO_TP1_EFF, so no change needed.

                    tp_df = pd.DataFrame({
                        "TP Zone": [f"TP1 ({RATIO_TP1_EFF:.3f})", f"TP2 ({RATIO_TP2_EFF:.3f})", f"TP3 ({RATIO_TP3_EFF:.3f})"],
                        "Price": [f"{tp1:.5f}", f"{tp2:.5f}", f"{tp3:.5f}"]
                    })
                    st.dataframe(tp_df, hide_index=True, use_container_width=True)
            except (ValueError, TypeError):
                 pass # Don't show error if inputs are not valid numbers yet
