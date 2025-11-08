# ==============================================================================
#                      THE UNIVERSAL TOPSTEP TRADE PLANNER
#                      เวอร์ชันรองรับทุกขนาดบัญชี (50k, 100k, 150k)
# ==============================================================================

# ============================== 1. IMPORTS ====================================
import streamlit as st
from decimal import Decimal, InvalidOperation

# ============================== 2. PAGE CONFIGURATION =========================
st.set_page_config(
    page_title="Universal Futures Planner",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================== 3. DATA DEFINITIONS ===========================
# --- START: ฐานข้อมูลกฎของแต่ละขนาดบัญชี ---
ACCOUNT_RULES = {
    "50K Buying Power": {
        "start_balance": 50000.0,
        "profit_target": 3000.0,
        "max_loss_limit": 2000.0,
        "daily_loss_limit": 1000.0, # ค่ามาตรฐานของ Topstep
        "max_contracts": 5
    },
    "100K Buying Power": {
        "start_balance": 100000.0,
        "profit_target": 6000.0,
        "max_loss_limit": 3000.0,
        "daily_loss_limit": 2000.0, # ค่ามาตรฐานของ Topstep
        "max_contracts": 10
    },
    "150K Buying Power": {
        "start_balance": 150000.0,
        "profit_target": 9000.0,
        "max_loss_limit": 4500.0,
        "daily_loss_limit": 3000.0, # ค่ามาตรฐานของ Topstep
        "max_contracts": 15
    }
}
# --- END: ฐานข้อมูลกฎ ---

FUTURES_TICK_VALUES = {
    "ES": 12.50, "MES": 1.25, "NQ": 5.00, "MNQ": 0.50, "YM": 5.00, "MYM": 0.50,
    "RTY": 5.00, "M2K": 0.50, "CL": 10.00, "MCL": 1.00, "GC": 10.00, "MGC": 1.00,
    "SI": 25.00, "SIL": 5.00,
}

FUTURES_TICK_SIZES = {
    "ES": 0.25, "MES": 0.25, "NQ": 0.25, "MNQ": 0.25, "YM": 1.00, "MYM": 1.00,
    "RTY": 0.10, "M2K": 0.10, "CL": 0.01, "MCL": 0.01, "GC": 0.10, "MGC": 0.10,
    "SI": 0.005, "SIL": 0.005,
}

# ============================== 4. HELPER FUNCTIONS ===========================
def get_micro_version(symbol):
    if symbol.startswith("E") or symbol.startswith("R") or symbol.startswith("Y"):
        return "M" + symbol[1:] if len(symbol) > 1 else None
    if symbol == "GC": return "MGC"
    if symbol == "CL": return "MCL"
    if symbol == "SI": return "SIL"
    return None

# ============================== 5. MAIN APPLICATION ===========================
st.title("⚙️ Universal Futures Trade Planner")

# --- START: เพิ่มตัวเลือกขนาดบัญชี ---
account_selection = st.selectbox(
    "เลือกขนาดบัญชีของคุณ (Select Your Account Size)",
    options=list(ACCOUNT_RULES.keys())
)
# ดึงกฎของบัญชีที่เลือกมาใช้งาน
selected_rules = ACCOUNT_RULES[account_selection]
# --- END: เพิ่มตัวเลือกขนาดบัญชี ---

st.divider()

# --- ส่วน Input ทั้งหมด ---
with st.container(border=True):
    st.markdown(f"#### กรอกแผนการเทรดของคุณสำหรับบัญชี **{account_selection}**")
    
    col1, col2, col3 = st.columns(3)
    # (ลบช่องกรอก Risk ออก เพราะจะคำนวณอัตโนมัติ)
    with col1:
        standard_symbols = sorted([s for s in FUTURES_TICK_VALUES.keys() if not s.startswith("M")])
        symbol_index = standard_symbols.index("GC") if "GC" in standard_symbols else 0
        symbol = st.selectbox("เลือกสินทรัพย์", options=standard_symbols, index=symbol_index)
    with col2:
        direction = st.radio("ทิศทาง", ["Long", "Short"], horizontal=True)

    col4, col5 = st.columns(2)
    with col4:
        entry_price_str = st.text_input("ราคาเข้า (Entry Price)", placeholder="เช่น 2350.50")
    with col5:
        sl_price_str = st.text_input("ราคาหยุดขาดทุน (SL Price)", placeholder="เช่น 2345.50")

# --- ส่วนคำนวณและแสดงผล ---
if entry_price_str and sl_price_str and symbol:
    try:
        entry_price = Decimal(entry_price_str)
        sl_price = Decimal(sl_price_str)
        tick_size = Decimal(str(FUTURES_TICK_SIZES.get(symbol, 0.01)))

        if tick_size <= 0:
            st.error(f"Tick Size สำหรับ {symbol} ต้องมากกว่า 0")
        else:
            price_diff_sl = abs(entry_price - sl_price)
            sl_ticks = int(price_diff_sl / tick_size)
            
            # --- START: ทำให้การคำนวณทั้งหมดเป็นไดนามิก ---
            
            # 1. คำนวณความเสี่ยงที่แนะนำโดยอัตโนมัติ (จากกฎที่เลือก)
            daily_loss_limit = selected_rules['daily_loss_limit']
            recommended_risk_usd = daily_loss_limit * 0.25 # กฎ 25% (Safe Mode)
            
            st.info(f"**ความเสี่ยงที่แนะนำ (Recommended Risk):** `${recommended_risk_usd:,.2f}` (คำนวณจาก 25% ของ Daily Loss Limit: ${daily_loss_limit:,.0f})")

            # 2. คำนวณความเสี่ยงพื้นฐาน
            standard_tick_value = FUTURES_TICK_VALUES.get(symbol, 0)
            risk_per_standard = sl_ticks * standard_tick_value
            
            micro_symbol = get_micro_version(symbol)
            micro_tick_value = FUTURES_TICK_VALUES.get(micro_symbol, 0) if micro_symbol else 0
            risk_per_micro = sl_ticks * micro_tick_value if micro_tick_value > 0 else 0
            
            # 3. คำนวณจำนวน Contracts ที่แนะนำ
            recommended_contracts = 0
            contract_type = "N/A"
            
            if risk_per_micro > 0 and risk_per_micro <= recommended_risk_usd:
                contract_type = "Micro"
                recommended_contracts = int(recommended_risk_usd / risk_per_micro)
            elif risk_per_standard > 0 and risk_per_standard <= recommended_risk_usd:
                contract_type = "Standard"
                recommended_contracts = int(recommended_risk_usd / risk_per_standard)
            
            st.divider()

            # 4. แสดงผลและ Slider (โดยใช้ Max Contracts จากกฎที่เลือก)
            with st.container(border=True):
                st.subheader("ผลการวิเคราะห์และวางแผน")
                st.markdown(f"**ระยะ SL ที่คำนวณได้:** `{sl_ticks} Ticks`")
                
                final_contracts = 0
                total_risk_now = 0.0

                if contract_type == "Micro":
                    max_micro_contracts = selected_rules['max_contracts'] * 10
                    final_contracts = st.slider(f"ปรับจำนวน Contracts ({micro_symbol})", min_value=1, max_value=max_micro_contracts, value=recommended_contracts, step=1)
                    total_risk_now = final_contracts * risk_per_micro
                elif contract_type == "Standard":
                    max_std_contracts = selected_rules['max_contracts']
                    final_contracts = st.slider(f"ปรับจำนวน Contracts ({symbol})", min_value=1, max_value=max_std_contracts, value=recommended_contracts, step=1)
                    total_risk_now = final_contracts * risk_per_standard
                else:
                    st.error(f"Setup นี้มีความเสี่ยงสูงเกินไปสำหรับ 'Recommended Risk' (${recommended_risk_usd:,.2f}) แม้จะใช้ 1 Micro Contract ก็ตาม (เสี่ยง ${risk_per_micro:,.2f})")

                if final_contracts > 0:
                    st.success(f"**แผนปัจจุบัน:** เข้า **{final_contracts} {contract_type} Contracts** | **ความเสี่ยงรวม:** **${total_risk_now:,.2f}**")
                    
                    st.markdown("#### 🎯 ตารางเป้าหมายกำไร (Potential Targets):")
                    # ... (ส่วนตารางเหมือนเดิมทุกประการ) ...
                    rr_levels = [1, 2, 3, 4, 5, 6, 7]
                    target_data = []
                    for rr in rr_levels:
                        tp_ticks = sl_ticks * rr
                        price_diff_tp = Decimal(tp_ticks) * tick_size
                        tp_price = entry_price + price_diff_tp if direction == "Long" else entry_price - price_diff_tp
                        if contract_type == "Micro":
                            total_profit_now = final_contracts * (tp_ticks * micro_tick_value)
                        else:
                            total_profit_now = final_contracts * (tp_ticks * standard_tick_value)
                        target_data.append({
                            "RR": f"1:{rr}",
                            "TP Price": f"{tp_price:.{sl_price.as_tuple().exponent*(-1)}f}",
                            "Potential Profit": f"${total_profit_now:,.2f}"
                        })
                    st.dataframe(target_data, hide_index=True, use_container_width=True)
            # --- END: ทำให้การคำนวณทั้งหมดเป็นไดนามิก ---

    except (InvalidOperation, TypeError):
        st.warning("กรุณากรอกราคาเข้าและราคา SL ให้ถูกต้อง")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
