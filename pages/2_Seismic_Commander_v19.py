# -*- coding: utf-8 -*-
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io
import os
from datetime import datetime, timedelta
# --- 匯入 Google Sheets 連線套件 ---
from streamlit_gsheets import GSheetsConnection

# --- 1. 系統環境初始化 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1EroMSHZhUBFyoh3h5BgJ31ohXfYOzGaHnR68ITP2Dqw/edit?gid=719942266#gid=719942266"

st.set_page_config(page_title="地震儀 v35.0 - 戰略預警版", page_icon="🛡️", layout="wide")

# --- 2. 視覺風格 (加入手機與平板專屬媒體查詢 Media Queries) ---
st.markdown("""
<style>
    /* 引入現代專業金融級字型組合 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+TC:wght@400;500;700;900&family=JetBrains+Mono:wght@500;700;800&display=swap');
    
    /* 全局字型 */
    html, body, [class*="css"] { 
        font-family: 'Inter', 'Noto Sans TC', sans-serif; 
    }
    
    /* 👉 桌機版：表頭大數據 (Metric) 字體 */
    [data-testid="stMetricValue"] > div {
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    [data-testid="stColumn"]:nth-child(5) [data-testid="stMetricValue"] > div,
    [data-testid="column"]:nth-child(5) [data-testid="stMetricValue"] > div {
        font-size: 22px !important;
    }
    
    /* 戰術橫幅 (高質感漸層與玻璃擬態陰影) */
    .tactical-banner { 
        padding: 24px 32px; 
        border-radius: 16px; 
        color: white; 
        margin-bottom: 24px; 
        border-left: 8px solid rgba(255,255,255,0.8);
        box-shadow: 0 10px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1);
        letter-spacing: 0.5px;
    }
    .critical { background: linear-gradient(135deg, #7F1D1D 0%, #450A0A 100%); animation: pulse-border 2.5s infinite; }
    .caution { background: linear-gradient(135deg, #D97706 0%, #78350F 100%); }
    .normal { background: linear-gradient(135deg, #065F46 0%, #064E3B 100%); }
    
    @keyframes pulse-border { 
        0% { border-left-color: rgba(239, 68, 68, 0.3); } 
        50% { border-left-color: rgba(239, 68, 68, 1); } 
        100% { border-left-color: rgba(239, 68, 68, 0.3); } 
    }
    
    /* 推薦卡片 */
    .recommendation-card { 
        background: #FFFFFF; 
        color: #111827 !important; 
        border: 1px solid #E5E7EB; 
        padding: 24px; 
        border-radius: 16px; 
        margin-bottom: 16px; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03), 0 2px 4px -2px rgba(0,0,0,0.03); 
        border-top: 5px solid #3B82F6;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .recommendation-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 20px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
    }
    
    /* 勝率標籤 */
    .win-rate-tag { 
        font-family: 'JetBrains Mono', monospace; 
        font-size: 24px; 
        font-weight: 800; 
        color: #BE123C; 
        background: #FFF1F2;
        padding: 4px 12px;
        border-radius: 8px;
        display: inline-block;
        border: 1px solid #FFE4E6;
    }
    
    /* 價格網格佈局 */
    .price-grid { 
        display: grid; 
        grid-template-columns: 1fr 1fr; 
        gap: 12px; 
        margin-top: 16px; 
        font-size: 14px; 
        color: #374151; 
        background: #F8FAFC;
        padding: 14px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
    }
    .price-grid b { font-family: 'JetBrains Mono', monospace; font-size: 15px; letter-spacing: -0.5px; }

    /* =========================================================
       📱 手機與平板專屬優化 (螢幕寬度小於 768px 時自動觸發)
       ========================================================= */
    @media (max-width: 768px) {
        /* 1. 縮小頂部大數據指標字體，防止手機版面破圖 */
        [data-testid="stMetricValue"] > div { font-size: 20px !important; }
        [data-testid="stColumn"]:nth-child(5) [data-testid="stMetricValue"] > div,
        [data-testid="column"]:nth-child(5) [data-testid="stMetricValue"] > div {
            font-size: 14px !important;
        }
        
        /* 2. 戰術橫幅縮小內邊距與字體，保留重要資訊但不佔版面 */
        .tactical-banner { 
            padding: 16px; 
            margin-bottom: 16px; 
            border-left-width: 5px;
        }
        .tactical-banner div:first-child { font-size: 18px !important; }
        .tactical-banner div:last-child { font-size: 14px !important; }
        
        /* 3. 推薦卡片內部優化：價格網格改成單欄堆疊，確保數字不被切斷 */
        .price-grid { 
            grid-template-columns: 1fr; /* 強制改為單行堆疊 */
            gap: 8px; 
            padding: 10px;
        }
        .recommendation-card { padding: 16px; }
        .win-rate-tag { font-size: 18px; padding: 2px 8px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. 數據偵察引擎 (底層邏輯完全不變) ---
class MarketIntelligence:
    @staticmethod
    def get_market_status():
        data = {"f_oi": -40000, "margin": 163.75, "twd": 32.5, "vix": 15.0, "date": "同步中...", "margin_date": "同步中...", "status": "⚖️ 震盪模式", "risk_level": 1, "warnings": []}
        try:
            import urllib3
            urllib3.disable_warnings() 
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.taifex.com.tw/cht/3/futContractsDate' 
            }
            is_success = False
            for i in range(5):
                target_date = (datetime.now() - timedelta(days=i)).strftime("%Y/%m/%d")
                url = "https://www.taifex.com.tw/cht/3/futContractsDateDown"
                payload_tx = {"queryStartDate": target_date, "queryEndDate": target_date, "commodityId": "TXF"}
                payload_mtx = {"queryStartDate": target_date, "queryEndDate": target_date, "commodityId": "MXF"}
                res_tx = requests.post(url, data=payload_tx, headers=headers, timeout=15, verify=False)
                res_mtx = requests.post(url, data=payload_mtx, headers=headers, timeout=15, verify=False)
                
                if res_tx.status_code == 200 and len(res_tx.content) > 500:
                    if b"<html" in res_tx.content.lower(): continue 
                    df_tx = pd.read_csv(io.StringIO(res_tx.content.decode('big5')), encoding='big5')
                    df_mtx = pd.read_csv(io.StringIO(res_mtx.content.decode('big5')), encoding='big5')
                    data["f_oi"] = int(df_tx.iloc[2, 13]) + int(df_mtx.iloc[2, 13])
                    data["date"] = target_date[5:] + " (自動)" 
                    is_success = True
                    break
            if not is_success:
                data["warnings"].append("⚠️ 籌碼抓取失敗：期交所伺服器無回應或無最新資料。")
                data["date"] = datetime.now().strftime("%m/%d") + " (預設/讀取失敗)"
        except Exception as e: 
            data["warnings"].append(f"🐛 系統底層錯誤回報：{e}")
            data["date"] = datetime.now().strftime("%m/%d") + " (預設/系統異常)"

        try:
            import re
            url_margin = "https://www.macromicro.me/series/23204/taiwan-taiex-maintenance-margin"
            headers_margin = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            res_margin = requests.get(url_margin, headers=headers_margin, timeout=15)
            if res_margin.status_code == 200:
                match = re.search(r'([1-9][0-9]{2}\.[0-9]{2})%', res_margin.text)
                if match:
                    data["margin"] = float(match.group(1))
                    data["margin_date"] = datetime.now().strftime("%Y/%m/%d %H:%M") + " (自動)"
                else:
                    data["margin_date"] = datetime.now().strftime("%Y/%m/%d %H:%M") + " (預設/動態阻擋)"
        except Exception as e:
            data["warnings"].append(f"🐛 融資維持率連線失敗：{e}")
            data["margin_date"] = datetime.now().strftime("%Y/%m/%d %H:%M") + " (預設/連線失敗)"

        try:
            twd_df = yf.download("TWD=X", period="5d", progress=False)
            if not twd_df.empty: data["twd"] = round(float(twd_df['Close'].iloc[-1]), 2)
            vix_df = yf.download("^VIX", period="5d", progress=False)
            if not vix_df.empty: data["vix"] = round(float(vix_df['Close'].iloc[-1]), 2)
        except: pass
        
        if data["margin"] < 160: data["warnings"].append("🚨 **融資預警**：維持率低於 160% 警戒線，嚴防集體斷頭引發的多殺多賣壓。")
        if data["f_oi"] < -35000: data["warnings"].append("📉 **籌碼預警**：外資空單布防超過 3.5 萬口，指數上檔承壓沉重，反彈宜減碼。")
        if data["vix"] > 22: data["warnings"].append("⚠️ **波動預警**：VIX 恐慌指數飆升，市場避險情緒濃厚，波動將大幅加劇。")
        if data["twd"] > 32.2: data["warnings"].append("💸 **匯率預警**：台幣持續貶值趨勢，留意資金外流對權值股與高持股標定的衝擊。")

        if data["f_oi"] < -35000 or data["vix"] > 22 or data["margin"] < 160:
            data["status"], data["risk_level"] = "🔴 全面防禦", 4
        elif data["f_oi"] > -10000 and data["vix"] < 15:
            data["status"], data["risk_level"] = "🚀 積極進攻", 0
        else:
            data["status"], data["risk_level"] = "⚖️ 震盪模式", 1
            
        return data

# --- 4. 戰略分析引擎 (底層邏輯完全不變) ---
class CommanderAnalyst:
    @staticmethod
    def analyze(sid, market, name="未知", risk_m=1.0):
        try:
            symbol = f"{sid}.TW" if market == "台股" else sid.upper()
            df = yf.download(symbol, period="100d", progress=False)
            if df.empty and market == "台股": df = yf.download(f"{sid}.TWO", period="100d", progress=False)
            if df.empty: return None

            df['E8'] = df['Close'].ewm(span=8).mean(); df['E34'] = df['Close'].ewm(span=34).mean()
            df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
            curr = round(float(df['Close'].iloc[-1]), 2)
            e8, e34 = float(df['E8'].iloc[-1]), float(df['E34'].iloc[-1])
            vol, v_ma = float(df['Volume'].iloc[-1]), float(df['Vol_MA'].iloc[-1])
            
            is_startup = curr > e8 and e8 > e34 and vol > v_ma
            sweet_p = round(e34 * 1.005, 2); def_p = round(e34 * 0.985, 2)
            p_range = float(df.tail(60).High.max()) - float(df.tail(60).Low.min())
            target_p = round(curr + (p_range * 0.8), 2)
            rr = round((target_p - curr) / (curr - def_p), 2) if curr > def_p else 0
            
            prob = 40 + (15 if curr > e8 else -5) + (15 if e8 > e34 else 0)
            if risk_m < 0.5: prob *= 0.8

            if curr <= sweet_p: strat = "🎯 價格已進入甜甜價區間，建議分批建倉，嚴守防護位。"
            elif is_startup: strat = "🚀 啟動中但乖離較大，建議 30% 現價試單，其餘 50% 於甜甜價埋伏。"
            elif curr > e8 and rr >= 1.5: strat = "🚀 多頭動能確立，建議右側進場試單，參與主升段。"
            else: strat = "⏳ 價格離支撐尚遠，建議掛單於甜甜價附近耐心等待，保護資金安全。"

            return {
                "代碼": sid, "名稱": name, "目前價": curr, "甜甜價": sweet_p, "目標價": target_p, "防守價": def_p,
                "獲利機率": f"{int(prob)}%", "WinVal": prob, "盈虧比": rr, "啟動時間": "🔥 啟動中" if is_startup else "⏳ 等待中",
                "r_val": 1 if is_startup else 2, "操作策略": strat, "是否達標": "✅ 是" if curr <= sweet_p else "❌ 否", "市場": market
            }
        except: return None

# --- 5. 主程式 ---
def main():
    st.title("⚓ 地震儀 v35.0：終極戰術指揮部")
    
    if 'intel_data' not in st.session_state:
        with st.spinner("系統初始化：自動同步大盤環境數據中..."):
            st.session_state.intel_data = MarketIntelligence.get_market_status()
            if "margin_date" not in st.session_state.intel_data or st.session_state.intel_data["margin_date"] == "同步中...":
                st.session_state.intel_data["margin_date"] = datetime.now().strftime("%Y/%m/%d %H:%M") + " (預設)"

    # --- 側邊欄 (手機版會自動收合至左上角漢堡選單) ---
    st.sidebar.markdown("### 📊 大盤環境參數 (手動校正)")
    st.sidebar.caption(f"外資數據時間：{st.session_state.intel_data.get('date', '未知')}")
    m_foi = st.sidebar.number_input("外資未平倉 (口)", value=int(st.session_state.intel_data["f_oi"]), step=1000)
    st.sidebar.markdown("[🔗 前往期交所確認外資淨未平倉](https://www.taifex.com.tw/cht/3/futContractsDate)", unsafe_allow_html=True)
    st.sidebar.divider()
    st.sidebar.caption(f"維持率數據時間：{st.session_state.intel_data.get('margin_date', '未知')}")
    m_margin = st.sidebar.number_input("最新融資維持率 (%)", value=float(st.session_state.intel_data["margin"]), step=0.5)
    st.sidebar.markdown("[🔗 前往財經M平方確認維持率](https://www.macromicro.me/series/23204/taiwan-taiex-maintenance-margin)", unsafe_allow_html=True)
    st.sidebar.divider()
    
    if m_foi != st.session_state.intel_data["f_oi"] or m_margin != st.session_state.intel_data["margin"]:
        st.session_state.intel_data["f_oi"] = m_foi
        st.session_state.intel_data["margin"] = m_margin
        if m_foi < -35000 or st.session_state.intel_data["vix"] > 22 or m_margin < 160:
            st.session_state.intel_data["status"], st.session_state.intel_data["risk_level"] = "🔴 全面防禦", 4
        elif m_foi > -10000 and st.session_state.intel_data["vix"] < 15:
            st.session_state.intel_data["status"], st.session_state.intel_data["risk_level"] = "🚀 積極進攻", 0
        else:
            st.session_state.intel_data["status"], st.session_state.intel_data["risk_level"] = "⚖️ 震盪模式", 1
        st.rerun()

    intel = st.session_state.intel_data
    risk_m = 1.0 if intel['risk_level'] < 4 else 0.3
    
    # A. 數據儀表板 (Streamlit 在手機版會自動將 st.columns 堆疊，搭配我們上方寫好的字體縮小 CSS 完美呈現)
    m_cols = st.columns(5)
    m_cols[0].metric("融存維持率", f"{intel['margin']}%", delta="-1.5%" if intel['margin'] < 160 else "穩定")
    m_cols[1].metric("外資未平倉", f"{intel['f_oi']:,} 口", help="大台+小台加總")
    m_cols[2].metric("台幣匯率", f"{intel['twd']}", delta="貶值" if intel['twd'] > 32.2 else "升值")
    m_cols[3].metric("VIX 恐慌指數", f"{intel['vix']}", delta="風險飆升" if intel['vix'] > 20 else "穩定", delta_color="inverse")
    m_cols[4].metric("數據基準日期", intel['date'])

    # B. 戰術橫幅
    style = "critical" if intel['risk_level'] >= 4 else ("caution" if intel['risk_level'] >= 1 else "normal")
    banner_text = "🔴 全面防禦：執行 1-6-3 防禦陣型，暫停放大部位並大幅提高現金比例至六成以上，若跌破防守價應果斷離場避開斷頭潮。" if risk_m < 0.5 else \
                  "🟢 環境穩定：執行 3-5-2 佈局，分批於甜甜價位階進場埋伏，嚴守 34MA 指數均線防禦，在具備盈虧比優勢下可積極參與波動。"
    st.markdown(f'<div class="tactical-banner {style}"><div style="font-size: 24px; font-weight: 900;">【{intel["status"]}】環境倍率: {risk_m}</div><div style="margin-top:10px; font-size:16px;">{banner_text}</div></div>', unsafe_allow_html=True)

    if intel["warnings"]:
        for msg in intel["warnings"]:
            st.warning(msg)

    # D. 側邊欄：手動診斷 HUD 與資金計算機
    with st.sidebar:
        st.header("🎯 戰略配置與診斷")
        total_cap = st.number_input("預備作戰總資金 (TWD)", value=9000000, step=100000)
        st.divider()
        m_id = st.text_input("輸入代碼 (2330 / NVDA)").upper()
        m_mkt = st.selectbox("市場", ["台股", "美股"])
        if m_id:
            res = CommanderAnalyst.analyze(m_id, m_mkt, risk_m=risk_m)
            if res:
                st.metric("分析勝率", res['獲利機率'], delta=res['啟動時間'])
                st.write(f"📈 現價: {res['目前價']} | 🍯 甜甜: {res['甜甜價']}")
                st.write(f"🎯 目標: {res['目標價']} | 🛡️ 防守: {res['防守價']}")
                unit_cap = total_cap * 0.05 * risk_m
                shares = int(unit_cap / (res['目前價'] * (intel['twd'] if m_mkt == "美股" else 1)))
                st.write(f"💰 單筆上限：{unit_cap:,.0f} TWD")
                st.success(f"📊 建議買進：{shares:,} 股")
                
                if st.button("➕ 一鍵加入監控清單"):
                    conn = st.connection("gsheets", type=GSheetsConnection)
                    try:
                        df = conn.read(spreadsheet=SHEET_URL)
                        if df.empty or '代碼' not in df.columns:
                            df = pd.DataFrame(columns=['代碼', '名稱', '市場', '戰略定位'])
                        
                        if not str(m_id) in df['代碼'].astype(str).values:
                            new_row = pd.DataFrame([{'代碼': m_id, '名稱': '手動新增', '市場': m_mkt, '戰略定位': ''}])
                            updated_df = pd.concat([df, new_row], ignore_index=True)
                            conn.update(spreadsheet=SHEET_URL, data=updated_df)
                            st.toast(f"已加入雲端 {m_id}")
                        else:
                            st.warning(f"{m_id} 已在雲端清單中")
                    except Exception as e:
                        st.error(f"寫入雲端失敗: {e}")

    # E. 清單同步與顯示 (手機版表格會自動支援手指左右滑動)
    if st.button("🔄 同步全球巡檢清單資料"):
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            df_raw = conn.read(spreadsheet=SHEET_URL)
            df_raw = df_raw.dropna(subset=['代碼']) 
            if not df_raw.empty:
                all_res = []; bar = st.progress(0)
                for i, row in df_raw.iterrows():
                    name_val = row['名稱'] if '名稱' in df_raw.columns else "未知"
                    r = CommanderAnalyst.analyze(row['代碼'], row['市場'], name_val, risk_m=risk_m)
                    if r: all_res.append(r)
                    bar.progress((i+1)/len(df_raw))
                st.session_state.v35_all = pd.DataFrame(all_res)
        except Exception as e:
            st.error(f"讀取雲端清單失敗: {e}")

    if 'v35_all' in st.session_state:
        df = st.session_state.v35_all
        st.subheader("🚀 十日強攻先鋒：台美精選 Top 5")
        
        # Streamlit 內建 RWD 特性：在桌機維持雙欄，在手機 (<768px) 會自動解除強制分欄並上下堆疊
        c1, c2 = st.columns(2)
        for i, mkt in enumerate(["台股", "美股"]):
            with [c1, c2][i]:
                st.markdown(f"#### {'🇹🇼' if mkt=='台股' else '🇺🇸'} {mkt}標的")
                top_5 = df[df['市場']==mkt].sort_values(["是否達標", "r_val", "WinVal"], ascending=[False, True, False]).head(5)
                for _, r in top_5.iterrows():
                    st.markdown(f"""<div class="recommendation-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="win-rate-tag">{r['獲利機率']}</span><span style="font-weight:900;">{r['代碼']} {r['名稱']}</span>
                        </div>
                        <div class="price-grid">
                            <span>📈 現價: <b>{r['目前價']}</b></span><span>🍯 甜甜: <b style="color:#059669;">{r['甜甜價']}</b></span>
                            <span>🎯 目標: <b style="color:#2563eb;">{r['目標價']}</b></span><span>🛡️ 防守: <b style="color:#dc2626;">{r['防守價']}</b></span>
                        </div>
                        <div style="margin-top:8px; font-weight:700; color:#3b82f6; font-size:14px;">{r['操作策略']}</div>
                    </div>""", unsafe_allow_html=True)
        st.divider()
        st.subheader("📋 全球巡檢部署清單")
        show_sweet = st.checkbox("🎯 只顯示現價 <= 甜甜價 (已達標標的)")
        df_display = df[df['目前價'] <= df['甜甜價']] if show_sweet else df
        sorted_table = df_display.sort_values("WinVal", ascending=False)[["代碼", "名稱", "市場", "目前價", "甜甜價", "目標價", "防守價", "盈虧比", "獲利機率", "啟動時間", "操作策略"]]
        # use_container_width=True 確保在手機上自動出現水平滾動條，完美適配小螢幕
        st.dataframe(sorted_table, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()