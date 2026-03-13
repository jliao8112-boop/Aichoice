# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
# --- 匯入 Google Sheets 連線套件 ---
from streamlit_gsheets import GSheetsConnection

# --- 1. 系統環境與自動初始化 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1EroMSHZhUBFyoh3h5BgJ31ohXfYOzGaHnR68ITP2Dqw/edit?gid=719942266#gid=719942266"

st.set_page_config(page_title="模組 S：戰略指揮官 v19.2", page_icon="🛡️", layout="wide")

# --- 2. 旗艦級專業視覺 CSS (加入手機版 RWD 優化) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Noto+Sans+TC:wght@500;700;900&family=JetBrains+Mono:wght@600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', 'Noto Sans TC', sans-serif; background-color: #F8FAFC; color: #1E293B; }

    .danger-zone {
        background: linear-gradient(90deg, #0F172A 0%, #1E293B 100%);
        color: #F8FAFC; padding: 24px; border-radius: 16px; margin-bottom: 25px;
        border-left: 10px solid #3B82F6; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    }
    
    @keyframes pulse-border {
        0% { border-left-color: #E11D48; box-shadow: 0 0 0 0 rgba(225, 29, 72, 0.4); }
        70% { border-left-color: #9F1239; box-shadow: 0 0 0 10px rgba(225, 29, 72, 0); }
        100% { border-left-color: #E11D48; box-shadow: 0 0 0 0 rgba(225, 29, 72, 0); }
    }
    .critical-zone {
        background: linear-gradient(90deg, #4C0519 0%, #1C1917 100%);
        color: #F8FAFC; padding: 24px; border-radius: 16px; margin-bottom: 25px;
        border-left: 10px solid #E11D48; box-shadow: 0 10px 15px -3px rgba(225, 29, 72, 0.3);
        animation: pulse-border 2s infinite;
    }
    .critical-text { color: #FECACA; font-weight: 800; font-size: 1.15rem; margin-top: 10px; line-height: 1.5; }
    
    .intelligence-box {
        background: #ffffff; border: 1px solid #E2E8F0; border-radius: 12px;
        padding: 18px; margin-bottom: 25px; font-size: 0.95rem; line-height: 1.6; color: #334155;
        border-left: 5px solid #64748B;
    }

    .vanguard-card {
        background: #ffffff; border-radius: 16px; padding: 22px; margin-bottom: 20px;
        border: 1px solid #CBD5E1; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        position: relative; overflow: hidden;
    }
    .tw-tag-strip { position: absolute; top: 0; left: 0; width: 100%; height: 6px; background: #E11D48; }
    .us-tag-strip { position: absolute; top: 0; left: 0; width: 100%; height: 6px; background: #2563EB; }

    .card-title { font-size: 1.4rem; font-weight: 900; color: #0F172A; margin: 0; }
    .card-subtitle { font-size: 0.85rem; color: #64748B; font-weight: 700; margin-top: 4px; }

    .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 15px; }
    .metric-item { background: #F8FAFC; padding: 10px; border-radius: 10px; border: 1px solid #F1F5F9; }
    .metric-label { color: #64748B; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; }
    .metric-value { font-family: 'JetBrains Mono'; font-size: 1.25rem; font-weight: 800; color: #0F172A; }
    .tw-val { color: #BE123C !important; }
    .us-val { color: #1D4ED8 !important; }

    .progress-container { margin-top: 15px; }
    .progress-label { display: flex; justify-content: space-between; font-size: 0.75rem; font-weight: 800; color: #334155; }
    .progress-bg { background: #E2E8F0; border-radius: 10px; height: 10px; margin-top: 5px; overflow: hidden; }
    .fill-tw { background: linear-gradient(90deg, #E11D48, #FB7185); height: 100%; }
    .fill-us { background: linear-gradient(90deg, #2563EB, #3B82F6); height: 100%; }

    .sidebar-hud {
        background: white; padding: 12px; border-radius: 10px; border: 1px solid #E2E8F0;
        margin-bottom: 10px; border-left: 5px solid #3B82F6;
    }
    .hud-label { color: #64748B; font-size: 0.7rem; font-weight: 800; }
    .hud-value { color: #0F172A; font-size: 1.1rem; font-weight: 800; font-family: 'JetBrains Mono'; }
    .currency-tag { font-size: 0.6em; color: #94A3B8; margin-right: 3px; }

    /* --- 新增：將價格區塊模組化 --- */
    .price-display { display: flex; justify-content: space-between; background: #F8FAFC; padding: 10px; border-radius: 8px; margin-top: 15px; border: 1px solid #F1F5F9; }
    .price-box { text-align: center; }
    .price-label { font-size: 0.65rem; color: #64748B; font-weight: 800; }
    .price-val { font-size: 0.9rem; font-weight: 800; font-family: 'JetBrains Mono'; }
    .action-box { margin-top:12px; padding: 8px; border-radius: 6px; border: 1px solid; font-size: 0.8rem; }

    /* =========================================================
       📱 手機與平板專屬優化 (螢幕寬度小於 768px 時自動觸發)
       ========================================================= */
    @media (max-width: 768px) {
        .danger-zone, .critical-zone { padding: 16px; margin-bottom: 15px; border-left-width: 6px; }
        .danger-zone h2, .critical-zone h2 { font-size: 1.3rem !important; }
        .critical-text { font-size: 1rem; }
        .vanguard-card { padding: 16px; margin-bottom: 15px; }
        
        /* 💡 核心魔法：讓橫排的 4 個價格，變成 2x2 的網格，絕對不破版 */
        .price-display { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: transparent; padding: 0; border: none; }
        .price-box { background: #F8FAFC; padding: 8px; border-radius: 6px; border: 1px solid #E2E8F0; }
        
        .action-box { font-size: 0.75rem; }
        .metric-value { font-size: 1.1rem; }
        .intelligence-box { font-size: 0.85rem; padding: 14px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 數據偵察連：自動同步籌碼、維持率與大盤動能 ---
class MarketDataSync:
    @staticmethod
    def fetch_all():
        data = {"f_oi": -40462, "t_oi": 30000, "margin": 163.75, "date": "等待同步...", "margin_date": "等待同步...", "tw_ret": 0.0, "us_ret": 0.0}
        
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            for i in range(5):
                target_date = (datetime.now() - timedelta(days=i)).strftime("%Y/%m/%d")
                url_tx = f"https://www.taifex.com.tw/cht/3/futContractsDateDown?queryStartDate={target_date}&queryEndDate={target_date}&commodityId=TXF"
                url_mtx = f"https://www.taifex.com.tw/cht/3/futContractsDateDown?queryStartDate={target_date}&queryEndDate={target_date}&commodityId=MXF"
                
                res_tx = requests.get(url_tx, headers=headers, timeout=5)
                res_mtx = requests.get(url_mtx, headers=headers, timeout=5)
                
                if res_tx.status_code == 200 and len(res_tx.content) > 100 and b'html' not in res_tx.content[:100].lower():
                    df_tx = pd.read_csv(io.StringIO(res_tx.content.decode('big5')), encoding='big5')
                    df_mtx = pd.read_csv(io.StringIO(res_mtx.content.decode('big5')), encoding='big5')
                    
                    tx_oi = int(str(df_tx.iloc[2, 13]).replace(',', '').strip())
                    mtx_oi = int(str(df_mtx.iloc[2, 13]).replace(',', '').strip())
                    
                    f_oi_total = tx_oi + mtx_oi
                    data["f_oi"] = f_oi_total
                    data["date"] = f"{target_date} (自動)"
                    break
        except Exception: 
            data["date"] = datetime.now().strftime("%Y/%m/%d") + " (預設/讀取失敗)"
            
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            url_margin = "https://www.macromicro.me/series/23204/taiwan-taiex-maintenance-margin"
            res_m = requests.get(url_margin, headers=headers, timeout=8)
            if res_m.status_code == 200:
                soup = BeautifulSoup(res_m.text, 'html.parser')
                text_content = soup.get_text()
                match = re.search(r'維持率.*?([1-2]\d{2}\.\d{1,2})', text_content)
                if match: 
                    data["margin"] = float(match.group(1))
                    data["margin_date"] = datetime.now().strftime("%Y/%m/%d") + " (自動)"
                else:
                    data["margin"] = 163.75
                    data["margin_date"] = datetime.now().strftime("%Y/%m/%d") + " (預設/網頁阻擋)"
        except Exception: 
            data["margin"] = 163.75
            data["margin_date"] = datetime.now().strftime("%Y/%m/%d") + " (預設/連線失敗)"
        
        try:
            tw_df = yf.download("^TWII", period="40d", progress=False, threads=False)
            if len(tw_df) >= 20: data["tw_ret"] = float((tw_df['Close'].iloc[-1] - tw_df['Close'].iloc[-20]) / tw_df['Close'].iloc[-20])
        except Exception: pass
        try:
            us_df = yf.download("^GSPC", period="40d", progress=False, threads=False)
            if len(us_df) >= 20: data["us_ret"] = float((us_df['Close'].iloc[-1] - us_df['Close'].iloc[-20]) / us_df['Close'].iloc[-20])
        except Exception: pass

        return data

# --- 4. 戰略引擎核心 ---
class StrategicEngine:
    def __init__(self, m_data):
        self.f_oi = m_data["f_oi"]
        self.margin = m_data["margin"]
        self.tw_ret = m_data["tw_ret"]
        self.us_ret = m_data["us_ret"]
        
        self.is_bear = self.margin < 160 or self.f_oi < -30000 
        self.is_bull = self.margin >= 165 and self.f_oi > -10000

    def get_stock_info(self, sid):
        clean_sid = str(sid).strip().upper()
        is_us = any(c.isalpha() for c in clean_sid)
        search_list = [clean_sid] if is_us else [f"{clean_sid}.TW", f"{clean_sid}.TWO"]
        for sym in search_list:
            try:
                ticker = yf.Ticker(sym)
                info = ticker.info
                name = info.get('shortName') or info.get('longName')
                if name: return name, ("美股" if is_us else "台股")
            except: continue
        return "", ("美股" if is_us else "台股")

    def analyze(self, sid, user_name=""):
        try:
            clean_sid = str(sid).strip().upper()
            is_us = any(c.isalpha() for c in clean_sid)
            market, curr = ("美股", "US$") if is_us else ("台股", "NT$")
            symbol = clean_sid if is_us else f"{clean_sid}.TW"
            df = yf.download(symbol, period="100d", progress=False, threads=False)
            if (df is None or df.empty) and not is_us:
                df = yf.download(f"{clean_sid}.TWO", period="100d", progress=False, threads=False)
            if df is None or df.empty: return None
            
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df = df.astype(float).dropna()
            
            df['E8'] = df['Close'].ewm(span=8, adjust=False).mean()
            df['E34'] = df['Close'].ewm(span=34, adjust=False).mean()
            df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
            
            df['H-L'] = df['High'] - df['Low']
            df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
            df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
            df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
            df['ATR5'] = df['TR'].rolling(5).mean()
            df['ATR20'] = df['TR'].rolling(20).mean()
            
            latest = df.iloc[-1]
            open_p, close = float(latest['Open']), float(latest['Close'])
            e8, e34 = float(latest['E8']), float(latest['E34'])
            vol, vol_ma = float(latest['Volume']), float(latest['Vol_MA'])
            atr5, atr20 = float(latest['ATR5']), float(latest['ATR20'])
            
            is_red_candle = close > open_p
            
            stock_ret_20d = (close - float(df['Close'].iloc[-20])) / float(df['Close'].iloc[-20]) if len(df) >= 20 else 0
            mkt_ret_20d = self.us_ret if is_us else self.tw_ret
            is_rs_strong = stock_ret_20d > mkt_ret_20d
            
            is_vcp = atr5 < (atr20 * 0.75)

            if close > e8 and e8 > e34 and vol > vol_ma: 
                rise_time = "🔥 啟動中 (1-2日)"
            elif close > e34 and vol < vol_ma * 0.8: 
                rise_time = "🌟 VCP收斂 (即將表態)" if is_vcp else "⏳ 量縮末端 (3-5日)"
            elif close < e8 and close > e34: 
                rise_time = "🌀 回測蓄勢 (5-8日)"
            else: 
                rise_time = "💤 觀察築底 (10日+)"

            if not is_rs_strong and "🔥" not in rise_time:
                rise_time += " 🐢弱勢"

            prob = 40 + (15 if close > e8 else -10) + (10 if e8 > e34 else 0)
            prob += 15 if is_rs_strong else -10
            prob += 10 if is_vcp else 0
            
            if not is_us: prob = prob * (0.8 if self.f_oi < -35000 else 1.0)
            prob = int(min(max(prob, 10), 95))
            
            p_range = float(df.tail(60)['High'].max()) - float(df.tail(60)['Low'].min())
            target_p = round(close + (p_range * 0.8), 2)
            max_gain = round(((target_p - close) / close) * 100, 1)

            def_p = round(e34 * 0.985, 2)
            risk = close - def_p
            reward = target_p - close
            rr_ratio = round(reward / risk, 2) if risk > 0 else 0.0

            if self.is_bear: alloc_c, alloc_s, alloc_d = 10, 60, 30
            elif self.is_bull: alloc_c, alloc_s, alloc_d = 40, 40, 20
            else: alloc_c, alloc_s, alloc_d = 30, 50, 20
            
            return {
                "市場": market, "幣值": curr, "代碼": clean_sid, "名稱": user_name,
                "現價": round(close, 2), "甜甜價": round(e34 * 1.005, 2), "目標價": target_p, "防守價": def_p,
                "上漲預估": rise_time, "上漲機率": f"{prob}%", "最高幅度": max_gain,
                "prob_val": prob, "gain_val": max_gain, "乖離": round(((close-e34)/e34)*100, 1),
                "is_us": is_us, "price_vs_e8": close > e8, "e8_vs_e34": e8 > e34,
                "配置_現": f"{alloc_c}%", "配置_甜": f"{alloc_s}%", "配置_防": f"{alloc_d}%",
                "盈虧比": rr_ratio, "is_rs_strong": is_rs_strong, "is_vcp": is_vcp,
                "is_red_candle": is_red_candle
            }
        except: return None

# --- 5. 主 UI 流程 ---
def main():
    if 'm_data' not in st.session_state:
        with st.spinner("自動部署：雙引擎數據偵察連啟動中..."):
            st.session_state.m_data = MarketDataSync.fetch_all()
            
    if 'refresh_main' not in st.session_state: 
        st.session_state.refresh_main = True

    # --- 側邊欄大盤參數手動校正與連結 ---
    st.sidebar.markdown("### 📊 大盤環境參數 (自動與手動校正)")
    
    st.sidebar.caption(f"外資數據時間：{st.session_state.m_data.get('date', '未知')}")
    m_foi = st.sidebar.number_input("外資未平倉 (口)", value=int(st.session_state.m_data["f_oi"]), step=1000)
    st.sidebar.markdown("[🔗 前往期交所確認外資淨未平倉](https://www.taifex.com.tw/cht/3/futContractsDate)", unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    st.sidebar.caption(f"維持率數據時間：{st.session_state.m_data.get('margin_date', '未知')}")
    m_margin = st.sidebar.number_input("最新融資維持率 (%)", value=float(st.session_state.m_data["margin"]), step=0.5)
    st.sidebar.markdown("[🔗 前往財經M平方確認維持率](https://www.macromicro.me/series/23204/taiwan-taiex-maintenance-margin)", unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    if m_foi != st.session_state.m_data["f_oi"] or m_margin != st.session_state.m_data["margin"]:
        st.session_state.m_data["f_oi"] = m_foi
        st.session_state.m_data["margin"] = m_margin
        st.rerun()
    
    engine = StrategicEngine(st.session_state.m_data)
    
    if 'fetched_name' not in st.session_state: st.session_state.fetched_name = ""
    if 'last_sid' not in st.session_state: st.session_state.last_sid = ""

    if engine.is_bear:
        banner_class = "critical-zone"
        title_icon = "🚨"
        status_text = f"<div class='critical-text'>⚠️ 警告：系統偵測到高度不可預期風險！外資期貨 {engine.f_oi} 口 | 維持率 {engine.margin}%<br>🛑 指令：強烈建議暫停放大部位，嚴守停損，現金水位拉高至 60% 以上！</div>"
    else:
        banner_class = "danger-zone"
        title_icon = "🛡️"
        status_text = f"<div style='margin-top:10px; font-weight:800; font-size:1.1rem; opacity:0.9;'>外資期貨：{engine.f_oi} 口 | 融資維持率：{engine.margin}% | 狀態：{'🚀 進攻模式' if engine.is_bull else '⚖️ 震盪模式'}</div>"

    st.markdown(f"""
    <div class="{banner_class}">
        <h2 style='margin:0; font-size:1.6rem;'>{title_icon} 模組 S：戰略指揮官 v19.2</h2>
        {status_text}
    </div>
    <div class="intelligence-box">
        <b>🕵️ 趨勢大數據深度預測：</b><br>
        • <b>同步籌碼：</b> 系統已自動對接期交所，目前外資淨未平倉為 <b>{engine.f_oi} 口</b>。<br>
        • <b>防禦狀態：</b> {'🚨 指令：處於空方壓制期，嚴格執行 1-6-3 防守陣型，保留現金。' if engine.is_bear else ('🚀 指令：多方格局，執行 4-4-2 進攻陣型。' if engine.is_bull else '⚖️ 指令：盤勢震盪，維持標準 3-5-2 佈局陣型。')}<br>
        • <b>大盤維持率：</b> 最新數值為 <b>{engine.margin}%</b>{' (已跌破 160% 警戒線，嚴防斷頭殺盤)' if engine.margin < 160 else ' (籌碼尚屬穩定)'}。
    </div>
    """, unsafe_allow_html=True)

    if engine.is_bear:
        st.sidebar.error("🚨 **大盤高度警戒**\n\n系統性風險飆高，請管住雙手，嚴守防守價，切忌無腦攤平！")

    st.sidebar.markdown("### 🎯 首席診斷 HUD")
    m_sid = st.sidebar.text_input("輸入代碼 (2330 / PLTR)", key="sid_input").upper()
    if m_sid and m_sid != st.session_state.last_sid:
        name, _ = engine.get_stock_info(m_sid)
        st.session_state.fetched_name = name if name else ""
        st.session_state.last_sid = m_sid
    m_name = st.sidebar.text_input("股票名稱", value=st.session_state.fetched_name)
    m_pos = st.sidebar.text_input("戰略定位")
    
    if m_sid:
        res = engine.analyze(m_sid, user_name=m_name)
        if res:
            curr = res['幣值']
            st.sidebar.markdown(f"**{res['市場']} {res['代碼']}**")
            
            rr_color = "#059669" if res['盈虧比'] >= 1.5 else ("#D97706" if res['盈虧比'] >= 1.0 else "#DC2626")
            rr_icon = "⚖️" if res['盈虧比'] >= 1.5 else ("⚠️" if res['盈虧比'] >= 1.0 else "🚨")
            
            k_color = "#059669" if res['is_red_candle'] else "#64748B"
            k_text = "收紅K (右側確認)" if res['is_red_candle'] else "收黑K (仍在測底)"
            
            hud_items = [
                (f"💎 現價 ({res['配置_現']})", res['現價'], "#1E40AF"), 
                (f"🍯 甜甜價 ({res['配置_甜']})", res['甜甜價'], "#D97706"),
                (f"🛡️ 防守價 ({res['配置_防']})", res['防守價'], "#DC2626"),
                ("🎯 最高目標價", f"{res['目標價']}", "#059669"),
                ("🕯️ K棒狀態", k_text, k_color),
                ("⏳ 預估上漲", res['上漲預估'], "#6D28D9"),
                (f"{rr_icon} 盈虧比 (R/R)", res['盈虧比'], rr_color)
            ]
            
            for label, val, color in hud_items:
                if "目標價" in label:
                    v_str = f"<span class='currency-tag'>{curr}</span>{val} <span style='color:#BE123C; font-size:0.85em;'>(+{res['最高幅度']}%)</span>"
                    text_color = '#0F172A'
                else:
                    is_txt = "日" in str(val) or "盈虧比" in label or "VCP" in str(val) or "弱勢" in str(val) or "K棒" in label
                    v_str = f"{val}" if is_txt else f"<span class='currency-tag'>{curr}</span>{val}"
                    text_color = color if is_txt else '#0F172A'
                
                st.sidebar.markdown(f"""<div class="sidebar-hud" style="border-left-color:{color};"><div class="hud-label">{label}</div><div class="hud-value" style="color:{text_color};">{v_str}</div></div>""", unsafe_allow_html=True)
            
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🧮 贏家兵力風險計算機")
            capital = st.sidebar.number_input(f"預備作戰總資金 ({curr})", value=100000, step=10000)
            risk_pct = st.sidebar.number_input("單筆最高可承受虧損 (%)", value=2.0, step=0.5)
            
            if capital > 0:
                max_loss = capital * (risk_pct / 100)
                if res['現價'] > res['防守價']:
                    alloc_c_val = int(res['配置_現'].strip('%')) / 100
                    alloc_s_val = int(res['配置_甜'].strip('%')) / 100
                    alloc_d_val = int(res['配置_防'].strip('%')) / 100
                    
                    shares_c_cap = int((capital * alloc_c_val) / res['現價']) if res['現價'] > 0 else 0
                    shares_s_cap = int((capital * alloc_s_val) / res['甜甜價']) if res['甜甜價'] > 0 else 0
                    shares_d_cap = int((capital * alloc_d_val) / res['防守價']) if res['防守價'] > 0 else 0
                    
                    total_shares = shares_c_cap + shares_s_cap + shares_d_cap
                    total_cost = (shares_c_cap * res['現價']) + (shares_s_cap * res['甜甜價']) + (shares_d_cap * res['防守價'])
                    actual_risk = (shares_c_cap * (res['現價'] - res['防守價'])) + (shares_s_cap * (res['甜甜價'] - res['防守價']))
                    
                    st.sidebar.info(f"**🛡️ 紀律風控試算結果**\n\n"
                                    f"• 若全數停損將虧損：**{curr} {actual_risk:,.0f}**\n"
                                    f"• **安全可買總股數：{total_shares:,} 股**\n"
                                    f"• 現價試單 ({res['配置_現']})：**{shares_c_cap:,} 股**\n"
                                    f"• 甜甜價埋伏 ({res['配置_甜']})：**{shares_s_cap:,} 股**\n"
                                    f"• 防守線接刀 ({res['配置_防']})：**{shares_d_cap:,} 股**\n"
                                    f"• 預估投入總金額：**{curr} {total_cost:,.0f}**")
                    
                    if res['盈虧比'] < 1.0:
                        st.sidebar.error("🚨 **極高風險：** 盈虧比低於 1.0！強烈建議放棄！")
                    elif res['盈虧比'] < 1.5:
                        st.sidebar.warning("⚠️ **系統警告：** 盈虧比偏低。建議退守「甜甜價」埋伏！")
                else:
                    st.sidebar.warning("⚠️ 現價已低於或等於防守價，不建議建倉！")

            st.sidebar.markdown("---")
            if st.sidebar.button("➕ 一鍵加入監控清單", use_container_width=True):
                conn = st.connection("gsheets", type=GSheetsConnection)
                try:
                    df = conn.read(spreadsheet=SHEET_URL)
                    if df.empty or '代碼' not in df.columns:
                        df = pd.DataFrame(columns=['代碼', '名稱', '市場', '戰略定位'])
                    
                    if not str(res['代碼']) in df['代碼'].astype(str).values:
                        new_row = pd.DataFrame([[res['代碼'], m_name, res['市場'], m_pos]], columns=['代碼', '名稱', '市場', '戰略定位'])
                        updated_df = pd.concat([df, new_row], ignore_index=True)
                        conn.update(spreadsheet=SHEET_URL, data=updated_df)
                        st.sidebar.success(f"已存入雲端：{m_name}")
                        st.session_state.refresh_main = True
                        st.rerun()
                    else:
                        st.sidebar.warning(f"{m_name} 已存在雲端清單中！")
                except Exception as e:
                    st.sidebar.error(f"寫入雲端失敗，請確認連線設定。錯誤：{e}")

    tab1, tab2 = st.tabs(["🚀 全球先鋒旗艦區 (5+5)", "📋 全球實時巡檢"])
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    try:
        watchlist = conn.read(spreadsheet=SHEET_URL)
        watchlist = watchlist.dropna(subset=['代碼'])
    except Exception as e:
        st.error(f"無法讀取雲端監控清單，請確認 API 金鑰與權限設定。錯誤訊息：{e}")
        watchlist = pd.DataFrame(columns=['代碼', '名稱', '市場', '戰略定位'])

    if not watchlist.empty:
        if 'watchlist_res' not in st.session_state or st.session_state.refresh_main:
            all_res = []
            with st.spinner("雲端資料同步與全球數據巡檢中..."):
                for _, row in watchlist.iterrows():
                    d = engine.analyze(row['代碼'], user_name=row['名稱'])
                    if d: d['定位'] = row['戰略定位']; all_res.append(d)
            st.session_state.watchlist_res = all_res
            st.session_state.refresh_main = False
        else:
            all_res = st.session_state.watchlist_res
        
        if all_res:
            df_all = pd.DataFrame(all_res)
            tw_top5 = df_all[df_all['市場'] == "台股"].sort_values(["prob_val", "gain_val"], ascending=False).head(5)
            us_top5 = df_all[df_all['市場'] == "美股"].sort_values(["prob_val", "gain_val"], ascending=False).head(5)

            with tab1:
                st.markdown("<h3 style='color:#0F172A;'>🔥 十日強攻先鋒：台股精銳 Top 5</h3>", unsafe_allow_html=True)
                cols_tw = st.columns(3)
                for i, (idx, row) in enumerate(tw_top5.iterrows()):
                    p_w = min(row['gain_val'] / 40 * 100, 100)
                    rr = row['盈虧比']
                    is_red = row.get('is_red_candle', False)
                    
                    if rr >= 1.5:
                        if is_red:
                            rr_icon, rr_bg, rr_border, rr_text, rr_action = "⚖️", "#ECFDF5", "#A7F3D0", "#059669", "✅ 盈虧比佳且收紅：右側分批建倉"
                        else:
                            rr_icon, rr_bg, rr_border, rr_text, rr_action = "🔪", "#FFFBEB", "#FDE68A", "#D97706", "⚠️ 盈虧比高但收黑：防接刀，等紅K"
                    elif rr >= 1.0:
                        if is_red:
                            rr_icon, rr_bg, rr_border, rr_text, rr_action = "⚠️", "#FFFBEB", "#FDE68A", "#D97706", "⏳ 肉少風險高：退守甜甜價"
                        else:
                            rr_icon, rr_bg, rr_border, rr_text, rr_action = "📉", "#FEF2F2", "#FECACA", "#DC2626", "📉 下跌測底中：退守甜甜價等紅K"
                    else:
                        rr_icon, rr_bg, rr_border, rr_text, rr_action = "🚨", "#FEF2F2", "#FECACA", "#DC2626", "🛑 乖極大：強烈建議觀望"

                    with cols_tw[i % 3]:
                        # --- 改良版 HTML 結構 (支援 RWD 網格) ---
                        card_html_tw = f"""
<div class="vanguard-card">
    <div class="tw-tag-strip"></div>
    <div class="card-title">{row['名稱']}</div>
    <div class="card-subtitle">#{row['代碼']} · {row['定位']}</div>
    <div class="price-display">
        <div class="price-box"><div class="price-label">💎 現價({row['配置_現']})</div><div class="price-val" style="color: #1E40AF;">{row['現價']}</div></div>
        <div class="price-box"><div class="price-label">🍯 甜甜價({row['配置_甜']})</div><div class="price-val" style="color: #D97706;">{row['甜甜價']}</div></div>
        <div class="price-box"><div class="price-label">🛡️ 防守({row['配置_防']})</div><div class="price-val" style="color: #DC2626;">{row['防守價']}</div></div>
        <div class="price-box"><div class="price-label">🎯 目標價</div><div class="price-val" style="color: #059669;">{row['目標價']}</div></div>
    </div>
    <div class="action-box" style="background: {rr_bg}; border-color: {rr_border};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight: 800; color: {rr_text};">{rr_icon} 盈虧比: {rr}</span>
            <span style="font-weight: 700; color: #334155;">{rr_action}</span>
        </div>
    </div>
    <div style="margin-top:12px; display:flex; justify-content:space-between;">
        <div><div class="metric-label">上漲機率</div><div class="metric-value tw-val">{row['上漲機率']}</div></div>
        <div style="text-align:right;"><div class="metric-label">發動預估</div><div style="color:#6D28D9; font-weight:800;">{row['上漲預估']}</div></div>
    </div>
    <div class="progress-container">
        <div class="progress-label"><span>📈 波段漲幅空間</span><span>+{row['gain_val']}%</span></div>
        <div class="progress-bg"><div class="fill-tw" style="width: {p_w}%;"></div></div>
    </div>
</div>
"""
                        st.markdown(card_html_tw, unsafe_allow_html=True)

                st.divider()
                st.markdown("<h3 style='color:#0F172A;'>🌎 全球動能先鋒：美股精選 Top 5</h3>", unsafe_allow_html=True)
                cols_us = st.columns(3)
                for i, (idx, row) in enumerate(us_top5.iterrows()):
                    p_w = min(row['gain_val'] / 50 * 100, 100)
                    rr = row['盈虧比']
                    is_red = row.get('is_red_candle', False)
                    
                    if rr >= 1.5:
                        if is_red:
                            rr_icon, rr_bg, rr_border, rr_text, rr_action = "⚖️", "#ECFDF5", "#A7F3D0", "#059669", "✅ 盈虧比佳且收紅：右側分批建倉"
                        else:
                            rr_icon, rr_bg, rr_border, rr_text, rr_action = "🔪", "#FFFBEB", "#FDE68A", "#D97706", "⚠️ 盈虧比高但收黑：防接刀，等紅K"
                    elif rr >= 1.0:
                        if is_red:
                            rr_icon, rr_bg, rr_border, rr_text, rr_action = "⚠️", "#FFFBEB", "#FDE68A", "#D97706", "⏳ 肉少風險高：退守甜甜價"
                        else:
                            rr_icon, rr_bg, rr_border, rr_text, rr_action = "📉", "#FEF2F2", "#FECACA", "#DC2626", "📉 下跌測底中：退守甜甜價等紅K"
                    else:
                        rr_icon, rr_bg, rr_border, rr_text, rr_action = "🚨", "#FEF2F2", "#FECACA", "#DC2626", "🛑 乖離極大：強烈建議觀望"

                    with cols_us[i % 3]:
                        card_html_us = f"""
<div class="vanguard-card">
    <div class="us-tag-strip"></div>
    <div class="card-title">{row['代碼']}</div>
    <div class="card-subtitle">{row['名稱']} · US${row['現價']}</div>
    <div class="price-display">
        <div class="price-box"><div class="price-label">💎 現價({row['配置_現']})</div><div class="price-val" style="color: #1E40AF;">{row['現價']}</div></div>
        <div class="price-box"><div class="price-label">🍯 甜甜價({row['配置_甜']})</div><div class="price-val" style="color: #D97706;">{row['甜甜價']}</div></div>
        <div class="price-box"><div class="price-label">🛡️ 防守({row['配置_防']})</div><div class="price-val" style="color: #DC2626;">{row['防守價']}</div></div>
        <div class="price-box"><div class="price-label">🎯 目標價</div><div class="price-val" style="color: #059669;">{row['目標價']}</div></div>
    </div>
    <div class="action-box" style="background: {rr_bg}; border-color: {rr_border};">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight: 800; color: {rr_text};">{rr_icon} 盈虧比: {rr}</span>
            <span style="font-weight: 700; color: #334155;">{rr_action}</span>
        </div>
    </div>
    <div style="margin-top:12px; display:flex; justify-content:space-between;">
        <div><div class="metric-label">上漲機率</div><div class="metric-value us-val">{row['上漲機率']}</div></div>
        <div style="text-align:right;"><div class="metric-label">發動預估</div><div style="color:#6D28D9; font-weight:800;">{row['上漲預估']}</div></div>
    </div>
    <div class="progress-container">
        <div class="progress-label"><span>🚀 潛力空間</span><span>+{row['gain_val']}%</span></div>
        <div class="progress-bg"><div class="fill-us" style="width: {p_w}%;"></div></div>
    </div>
</div>
"""
                        st.markdown(card_html_us, unsafe_allow_html=True)
            
            with tab2:
                st.dataframe(df_all.sort_values("prob_val", ascending=False), use_container_width=True, hide_index=True)

            st.sidebar.divider()
            
            # === 修復版：戰術診斷 ===
            st.sidebar.markdown("### 🔍 戰術診斷")
            # 強制將下拉選單裡的代碼全部轉為字串
            diag_sid = st.sidebar.selectbox("從清單選擇標的", watchlist['代碼'].astype(str).tolist())
            
            if st.sidebar.button("診斷未入選原因", use_container_width=True):
                # 比對時，強制雙方都用字串格式進行比對，消除型別錯亂
                target = next((item for item in all_res if str(item["代碼"]).strip() == str(diag_sid).strip()), None)
                
                if target:
                    threshold = tw_top5.iloc[-1] if not target['is_us'] else us_top5.iloc[-1]
                    st.sidebar.info(f"**診斷報告：{target['名稱']}**")
                    if target['prob_val'] < threshold['prob_val']:
                        reasons = []
                        if not target['price_vs_e8']: reasons.append("● 股價低於 E8 (短線趨勢偏弱)")
                        if not target['e8_vs_e34']: reasons.append("● 均線尚未多頭排列 (E8 < E34)")
                        if not target['is_us'] and engine.f_oi < -35000: reasons.append("● 受大盤外資空單壓制")
                        if not target.get('is_rs_strong', True): reasons.append("● RS相對弱勢")
                        if not target.get('is_vcp', False): reasons.append("● 波動尚未收斂")
                        st.sidebar.warning("【勝率不足】\n" + "\n".join(reasons))
                    elif target['gain_val'] < threshold['gain_val']:
                        st.sidebar.warning(f"【空間不足】\n● 漲幅空間 (+{target['gain_val']}%) 低於先鋒門檻")
                    else:
                        st.sidebar.success("該標的數據已達標。")
                else:
                    st.sidebar.error("⚠️ 系統無法在目前的巡檢結果中找到該標的，請確認是否已完成同步。")

    else:
        st.info("💡 指揮部提醒：請先在左側輸入代碼並『加入監控清單』以啟動全球巡檢。")

if __name__ == "__main__":
    main()