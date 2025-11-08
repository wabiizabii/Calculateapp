# ==============================================================================
#           THE ULTIMATE STANDALONE TOPSTEP FUTURES TRADE PLANNER
#                      เวอร์ชันไฟล์เดียวจบ (ตามที่คุณต้องการ)
# ==============================================================================

# ============================== 1. IMPORTS ====================================
import streamlit as st
from decimal import Decimal, InvalidOperation

# ============================== 2. PAGE CONFIGURATION =========================
st.set_page_config(
    page_title="Topstep Futures Planner",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================== 3. DATA DEFINITIONS ===========================
# (ข้อมูล Tick Value และ Tick Size ถูกย้ายมารวมในไฟล์นี้)
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
st.title("🔵 Topstep Futures Planner & Calculator")

# --- ส่วน Input ทั้งหมด ถูกย้ายมาจาก Sidebar และรวมไว้ในหน้าหลัก ---
with st.container(border=True):
    st.markdown("#### 1. กรอกแผนการเทรดของคุณ (Idea)")
    
    # Input สำหรับสถานะบัญชี (จำเป็นสำหรับคำนวณ Scaling Plan)
    col_status_1, col_status_2 = st.columns(2)
    with col_status_1:
        current_equity = st.number_input("ยอด Equity ปัจจุบัน ($)", min_value=0.0, value=50000.0, step=100.0, format="%.2f", key="ts_equity")
    with col_status_2:
        highest_equity = st.number_input("ยอด Equity สูงสุดที่เคยทำได้ ($)", min_value=50000.0, value=max(50000.0, current_equity), step=100.0, key="ts_highest_equity")
    
    st.divider()
    
    # Input สำหรับแผนการเทรด
    form_col1, form_col2 = st.columns(2)
    with form_col1:
        standard_symbols = sorted([s for s in FUTURES_TICK_VALUES.keys() if not s.startswith("M")])
        symbol_index = standard_symbols.index("GC") if "GC" in standard_symbols else 0
        symbol = st.selectbox("เลือกสินทรัพย์ (Standard)", options=standard_symbols, index=symbol_index)
    with form_col2:
         direction = st.radio("ทิศทาง (Direction)", ["Long", "Short"], horizontal=True)
    
    form_col3, form_col4 = st.columns(2)
    with form_col3:
        entry_price_str = st.text_input("ราคาเข้า (Entry Price)", placeholder="เช่น 2350.50")
    with form_col4:
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
            
            standard_tick_value = FUTURES_TICK_VALUES.get(symbol, 0)
            risk_per_standard = sl_ticks * standard_tick_value
            
            micro_symbol = get_micro_version(symbol)
            micro_tick_value = FUTURES_TICK_VALUES.get(micro_symbol, 0) if micro_symbol else 0
            risk_per_micro = sl_ticks * micro_tick_value if micro_tick_value > 0 else 0

            daily_loss_limit = 1000.0
            recommended_risk_usd = daily_loss_limit * 0.25 # กฎ 25% DDL
            
            recommended_contracts = 0
            contract_type = "N/A"
            
            if risk_per_micro > 0 and risk_per_micro <= recommended_risk_usd:
                contract_type = "Micro"
                recommended_contracts = int(recommended_risk_usd / risk_per_micro)
            elif risk_per_standard > 0 and risk_per_standard <= recommended_risk_usd:
                contract_type = "Standard"
                recommended_contracts = int(recommended_risk_usd / risk_per_standard)
            
            st.divider()
            with st.container(border=True):
                st.markdown("#### 2. ปรับขนาดและวางแผน (Sizing & Planning)")
                st.markdown(f"**ระยะ SL ที่คำนวณได้:** `{sl_ticks} Ticks`")
                
                if contract_type == "Micro":
                    contracts_allowed_by_plan = min(50, 2 * 10) if current_equity < 51500.0 else min(50, 3 * 10)
                    final_contracts = st.slider(f"ปรับจำนวน Contracts ({micro_symbol})", min_value=1, max_value=contracts_allowed_by_plan, value=recommended_contracts, step=1)
                    total_risk_now = final_contracts * risk_per_micro
                elif contract_type == "Standard":
                    contracts_allowed_by_plan = 2 if current_equity < 51500.0 else 3
                    final_contracts = st.slider(f"ปรับจำนวน Contracts ({symbol})", min_value=1, max_value=contracts_allowed_by_plan, value=recommended_contracts, step=1)
                    total_risk_now = final_contracts * risk_per_standard
                else:
                    st.error("Setup นี้มีความเสี่ยงสูงเกินไป แม้จะใช้ 1 Micro Contract ก็ตาม กรุณาหา Setup ใหม่")
                    final_contracts = 0
                    total_risk_now = 0

                if final_contracts > 0:
                    st.success(f"**แผนปัจจุบัน:** เข้า **{final_contracts} {contract_type} Contracts** | **ความเสี่ยงรวม:** **${total_risk_now:,.2f}**")
                    
                    st.markdown("#### 🎯 ตารางเป้าหมายกำไร (Potential Targets):")
                    rr_levels = [1, 2, 3, 4, 5, 6, 7]
                    target_data = []
                    
                    for rr in rr_levels:
                        tp_ticks = sl_ticks * rr
                        price_diff_tp = Decimal(tp_ticks) * tick_size
                        tp_price = entry_price + price_diff_tp if direction == "Long" else entry_price - price_diff_tp
                        
                        if contract_type == "Micro":
                            total_profit_now = final_contracts * (tp_ticks * micro_tick_value)
                        else: # Standard
                            total_profit_now = final_contracts * (tp_ticks * standard_tick_value)

                        target_data.append({
                            "RR": f"1:{rr}",
                            "TP Price": f"{tp_price:.{sl_price.as_tuple().exponent*(-1)}f}",
                            "Potential Profit": f"${total_profit_now:,.2f}"
                        })
                    
                    st.dataframe(target_data, hide_index=True, use_container_width=True)

    except (InvalidOperation, TypeError):
        st.warning("กรุณากรอกราคาเข้าและราคา SL ให้ถูกต้องเพื่อเริ่มการคำนวณ")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
