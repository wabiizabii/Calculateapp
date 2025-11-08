# ==============================================================================
#                      TOPSTEP FUTURES TRADE PLANNER
#                      เวอร์ชัน Minimalist (คำนวณเพียวๆ)
# ==============================================================================

# ============================== 1. IMPORTS ====================================
import streamlit as st
from decimal import Decimal, InvalidOperation

# ============================== 2. PAGE CONFIGURATION =========================
st.set_page_config(
    page_title="Futures Trade Planner",
    layout="centered", # เปลี่ยนเป็น centered เพื่อให้ดูกระชับขึ้น
    initial_sidebar_state="collapsed"
)

# ============================== 3. DATA DEFINITIONS ===========================
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
st.title("⚙️ Futures Trade Planner")
st.markdown("เครื่องมือคำนวณ Position Size และเป้าหมายกำไร (RR)")

with st.container(border=True):
    st.markdown("**1. กรอกแผนการเทรดของคุณ (Idea)**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_usd = st.number_input("ความเสี่ยงที่ยอมรับได้ ($)", min_value=1.0, value=100.0, step=10.0, help="งบขาดทุนของคุณสำหรับเทรดนี้")
    with col2:
        standard_symbols = sorted([s for s in FUTURES_TICK_VALUES.keys() if not s.startswith("M")])
        symbol_index = standard_symbols.index("GC") if "GC" in standard_symbols else 0
        symbol = st.selectbox("เลือกสินทรัพย์", options=standard_symbols, index=symbol_index)
    with col3:
        direction = st.radio("ทิศทาง", ["Long", "Short"], horizontal=True)

    col4, col5 = st.columns(2)
    with col4:
        entry_price_str = st.text_input("ราคาเข้า (Entry Price)", placeholder="เช่น 2350.50")
    with col5:
        sl_price_str = st.text_input("ราคาหยุดขาดทุน (SL Price)", placeholder="เช่น 2345.50")

# --- คำนวณและแสดงผล ---
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
            
            st.info(f"**ระยะ SL ที่คำนวณได้:** `{sl_ticks} Ticks`")
            
            standard_tick_value = FUTURES_TICK_VALUES.get(symbol, 0)
            risk_per_standard = sl_ticks * standard_tick_value
            
            micro_symbol = get_micro_version(symbol)
            micro_tick_value = FUTURES_TICK_VALUES.get(micro_symbol, 0) if micro_symbol else 0
            risk_per_micro = sl_ticks * micro_tick_value if micro_tick_value > 0 else 0
            
            st.markdown("#### ✅ คำแนะนำ Position Size:")
            
            # สมมติ Max Contracts สำหรับการคำนวณทั่วไป (สามารถปรับได้)
            contracts_allowed_by_plan_std = 5 
            contracts_allowed_by_plan_micro = 50

            if risk_per_standard > 0 and risk_per_standard <= risk_usd:
                allowed = int(risk_usd / risk_per_standard)
                final = min(allowed, contracts_allowed_by_plan_std)
                st.success(f"**คำแนะนำ:** คุณสามารถเทรด **{symbol} (Standard)** ได้ **{final} Contract(s)** (ความเสี่ยง ~${final * risk_per_standard:,.2f})")
            elif micro_symbol and risk_per_micro > 0 and risk_per_micro <= risk_usd:
                allowed = int(risk_usd / risk_per_micro)
                final = min(allowed, contracts_allowed_by_plan_micro)
                st.warning(f"**คำแนะนำ:** Setup นี้ไม่เหมาะกับ Standard แต่เทรด **{micro_symbol} (Micro)** ได้ **{final} Contract(s)** (ความเสี่ยง ~${final * risk_per_micro:,.2f})")
            else:
                st.error(f"**คำแนะนำ:** Setup นี้มีความเสี่ยงสูงเกินไปสำหรับงบประมาณ (${risk_usd:,.2f}) ของคุณ")

            st.markdown("#### 🎯 ตารางเป้าหมายกำไร (Potential Targets):")
            
            rr_levels = [1, 2, 3, 4, 5, 6, 7]
            target_data = []
            
            for rr in rr_levels:
                tp_ticks = sl_ticks * rr
                price_diff_tp = Decimal(tp_ticks) * tick_size
                tp_price = entry_price + price_diff_tp if direction == "Long" else entry_price - price_diff_tp
                
                profit_standard = tp_ticks * standard_tick_value
                profit_micro = tp_ticks * micro_tick_value if micro_tick_value > 0 else None

                target_data.append({
                    "RR": f"1:{rr}",
                    "TP Price": f"{tp_price:.{sl_price.as_tuple().exponent*(-1)}f}",
                    "Profit / 1 Std Contract": f"${profit_standard:,.2f}",
                    "Profit / 1 Micro Contract": f"${profit_micro:,.2f}" if profit_micro is not None else "N/A"
                })
            
            st.dataframe(target_data, hide_index=True, use_container_width=True)

    except (InvalidOperation, TypeError):
        st.warning("กรุณากรอกราคาเข้าและราคา SL ให้ถูกต้อง")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
