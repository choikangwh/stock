import os
import sys
import datetime
import pandas as pd
import yfinance as yf
from google import genai
from google.genai import types
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def get_gemini_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("="*60)
        print("GEMINI_API_KEY 환경변수가 설정되어 있지 않습니다.")
        api_key = input("Gemini API Key를 입력해주세요: ").strip()
        print("="*60)
        if not api_key:
            print("API Key가 입력되지 않아 프로그램을 종료합니다.")
            sys.exit(1)
        # 세션 내에서만 유지되도록 설정
        os.environ["GEMINI_API_KEY"] = api_key
    return api_key

def get_client():
    api_key = get_gemini_api_key()
    # google-genai SDK의 Client 초기화 (AQ. 키 및 AIzaSy 키 모두 호환)
    return genai.Client(api_key=api_key)

def get_ticker_by_name(stock_name, client):
    print(f"\n[1/4] '{stock_name}'의 Yahoo Finance Ticker를 찾는 중...")
    
    prompt = f"""
    Please search and return the Yahoo Finance ticker symbol for the company or stock named '{stock_name}'.
    Respond with ONLY the exact ticker symbol (e.g. AAPL, 005930.KS, TSLA, 000660.KS, NVDA, 1810.HK) and nothing else.
    If the stock is listed on a specific market, make sure the suffix is correct (e.g., .KS for KOSPI, .KQ for KOSDAQ, .T for Tokyo, etc.).
    Do not write any markdown blocks, quotes, or additional text. Just return the ticker string.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        ticker = response.text.strip().replace("`", "").replace("'", "").replace('"', '').strip()
        print(f"티커 확인 완료: {ticker}")
        return ticker
    except Exception as e:
        print(f"티커 검색 중 오류 발생: {e}")
        return None

def check_price_movement(ticker_symbol):
    print(f"[2/4] '{ticker_symbol}'의 최근 주가 변동 분석 중...")
    try:
        stock = yf.Ticker(ticker_symbol)
        history = stock.history(period="5d")
        if history.empty:
            return "알 수 없음", 0.0, 0.0
            
        if len(history) >= 2:
            prev_close = history['Close'].iloc[-2]
            last_close = history['Close'].iloc[-1]
            diff = last_close - prev_close
            pct_change = (diff / prev_close) * 100
            direction = "상승" if diff >= 0 else "하락"
            return direction, pct_change, last_close
        else:
            last_close = history['Close'].iloc[-1]
            return "보합", 0.0, last_close
    except Exception as e:
        print(f"주가 변동 조회 실패: {e}")
        return "알 수 없음", 0.0, 0.0

def fetch_financial_data(ticker_symbol):
    print(f"[3/4] '{ticker_symbol}'의 yfinance 재무 데이터 수집 중...")
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        company_name = info.get('longName') or info.get('shortName') or ticker_symbol
        currency = info.get('currency', 'USD')
        
        # 5년치 데이터 추출
        financials = stock.financials # 손익계산서
        balance_sheet = stock.balance_sheet # 대차대조표
        cashflow = stock.cashflow # 현금흐름표
        
        # 분기 데이터 추출 (TTM 계산용)
        q_financials = stock.quarterly_financials
        q_cashflow = stock.quarterly_cashflow
        
        # 밸류에이션 수집
        valuation_metrics = {
            'Current Price': info.get('currentPrice'),
            'Market Cap': info.get('marketCap'),
            'Trailing P/E': info.get('trailingPE'),
            'Forward P/E': info.get('forwardPE'),
            'P/S (Trailing)': info.get('priceToSalesTrailing12Months'),
            'P/B': info.get('priceToBook'),
            'EV/EBITDA': info.get('enterpriseToEbitda'),
            'Currency': currency
        }
        
        # 텍스트 형식으로 변환하여 LLM에 제공할 재무 데이터 생성
        financials_str = financials.to_string() if not financials.empty else "No annual financials available"
        balance_sheet_str = balance_sheet.to_string() if not balance_sheet.empty else "No annual balance sheet available"
        cashflow_str = cashflow.to_string() if not cashflow.empty else "No annual cash flow available"
        
        q_financials_str = q_financials.to_string() if not q_financials.empty else "No quarterly financials available"
        q_cashflow_str = q_cashflow.to_string() if not q_cashflow.empty else "No quarterly cash flow available"
        
        raw_data = f"""
        Company Name: {company_name}
        Ticker: {ticker_symbol}
        Currency: {currency}
        
        [Valuation Metrics]
        {valuation_metrics}
        
        [Financials (Annual)]
        {financials_str}
        
        [Balance Sheet (Annual)]
        {balance_sheet_str}
        
        [Cash Flow (Annual)]
        {cashflow_str}
        
        [Financials (Quarterly)]
        {q_financials_str}
        
        [Cash Flow (Quarterly)]
        {q_cashflow_str}
        """
        return company_name, raw_data, valuation_metrics
    except Exception as e:
        print(f"yfinance 재무 데이터 수집 오류 (일부 데이터를 수집하지 못했을 수 있습니다): {e}")
        return ticker_symbol, f"yfinance data collection had errors: {str(e)}", {}

def generate_report(stock_name, ticker, direction, pct_change, last_close, company_name, raw_financials, client):
    print(f"[4/4] Gemini 2.5 Pro (Search Grounding) 기반 종합 투자 분석 보고서 작성 중...")
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # google-genai SDK 방식의 Google Search Tool 활성화
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.2
    )
    
    prompt = f"""
    당신은 글로벌 투자은행의 수석 주식 애널리스트이자 포트폴리오 매니저입니다.
    다음 주식에 대해 실시간 뉴스 검색 및 수집된 재무제표 데이터를 결합하여 최고 품질의 한국어 종합 투자 분석 보고서를 작성해 주세요.
    보고서는 상세하고 객관적이며 데이터 기반(지난 5개년 회계연도 및 TTM 기준)이어야 합니다.
    
    [분석 대상 종목 정보]
    - 입력된 종목명: {stock_name}
    - Yahoo Finance 티커: {ticker}
    - 기업명: {company_name}
    - 최근 종가: {last_close}
    - 최근 2거래일 대비 주가 변동: {direction} ({pct_change:+.2f}%)
    - 현재 분석 기준 시간: {current_time}
    
    [yfinance 수집 원본 재무 데이터]
    {raw_financials}
    
    --------------------------------------------------
    [작성 요구사항]
    
    1. 최신 뉴스 실시간 검색 및 요약:
       - Google Search를 사용하여 해당 종목의 최신 뉴스(실시간)를 검색하세요.
       - 주가가 최근 {direction}한 원인(상승 이유 또는 하락 이유)을 분석하여 요약해 주세요.
       - 최근 뉴스들을 날짜별로 명확하게 요약하여 출력해 주세요.
       
    2. 아래 구조를 따르는 상세 "분석 보고서"를 작성해 주세요:
       
       요약:
       - 주요 긍정적 촉매(Positive Catalysts)와 주요 위험(Key Risks) 요약.
       
       1. 재무 성과 및 건전성:
          - 손익계산서 분석: 지난 5년 + TTM 동안의 매출 성장, 매출 총이익률, 영업 이익률 및 순이익률 추세를 분석합니다. (yfinance 데이터에 5개년 미만인 경우, 실시간 검색을 활용하여 지난 5개년 수치를 최대한 보완해 주세요.)
          - 대차대조표 분석: 회사의 부채 수준, 부채 대 자기자본 비율(D/E), 유동 비율(Current Ratio) 및 현금 포지션을 평가하고, 대차대조표가 종합적으로 강한지 약한지 결론을 내립니다.
          - 현금 흐름 분석: 영업 현금 흐름, 자본 지출(CapEx) 및 잉여 현금 흐름(FCF) 발생을 분석합니다. 회사가 지속적으로 FCF가 긍정적인지 평가합니다.
          
       2. 가치 평가 (Valuation):
          - 배수 분석: 회사의 현재 P/E, P/S, P/B 및 EV/EBITDA 비율을 다음 세 가지와 정량적으로 비교 분석합니다:
            (a) 회사의 자체 5년 평균 배수
            (b) 해당 업계 평균 배수
            (c) 상위 3개 직접 경쟁사(예: [Competitor A], [Competitor B], [Competitor C])의 배수
            (경쟁사 3곳을 직접 찾아서 구체적인 티커 및 배수를 비교해 주세요. yfinance에 없는 과거 평균이나 경쟁사 배수 등은 구글 검색을 활용하십시오.)
          - 결론: 이 분석을 바탕으로 주식이 현재 과대 평가(Overvalued), 과소 평가(Undervalued) 또는 적정 가격(Fairly valued)인지 결론을 내립니다.
          
       3. 비즈니스 모델 및 경쟁 우위:
          - 사업 부문: 회사의 핵심 사업 부문과 매출에 대한 각 부문의 기여도를 간략하게 설명합니다.
          - 경제적 해자(Moat): 경쟁 우위의 원천(예: 브랜드, 특허, 네트워크 효과, 원가 경쟁력)을 식별하고 설명합니다. 이 해자의 지속성과 강점을 평가합니다.
          
       4. 성장 전략 및 미래 전망:
          - 성장 동력: 미래 성장을 촉진할 것으로 예상되는 주요 촉매(예: 신제품, 시장 확장, 산업 동향)를 식별합니다.
          - 시장 기회: 총 유효 시장(TAM)과 회사가 더 큰 시장 점유율을 확보할 수 있는 잠재력을 분석합니다.
          
       5. 경영진 및 거버넌스:
          - 리더십: CEO 및 수석 경영진에 대한 간략한 개요를 제공합니다. 재임 기간과 실적에 대해 언급합니다.
          - 자본 배분: 자본 배분에 대한 경영진의 효율성을 평가합니다. 배당, 자사주 매입 및 M&A 활동과 관련된 정책을 검토합니다.
          - 내부자 소유: 내부자 소유(Insider Ownership) 수준을 기록 및 평가합니다.
          
       6. 위험 분석:
          - 특이적 위험(Idiosyncratic Risks): 회사와 관련된 상위 3가지 위험은 무엇입니까(예: 제품 실패, 핵심 인물 위험, 소송)?
          - 체계적 위험(Systematic Risks): 상위 3가지 외부 위험은 무엇입니까(예: 경기 침체, 금리/규제 변경, 경쟁적 혼란)?
          
       7. ETF 및 매크로 분석:
          - 시장 및 산업 분야의 중장기 변화 정보를 기술하십시오. 최신 자료 기반 매크로(금리, 물가, 고용, 정책, 지정학)의 변화, 섹터(반도체, 금융, 에너지 등 구조 변화)의 움직임을 고려합니다.
          
       8. 최종 권장 사항:
          - 위의 모든 사항을 최종 투자 결론으로 종합합니다. 현재 가격에서 기회와 위험의 균형을 바탕으로 간결한 정당성과 함께 매수(Buy)/보유(Hold)/매도(Sell) 등급을 명확히 명시해 주세요.
          
    3. 종합 요약 개요 및 투자 테제 (보고서 가장 위에 위치하거나 아래의 지정된 양식으로 제공해 주세요):
       - 보고서 전면에 회사의 사업에 대한 간략한 개요를 제공합니다.
       - 전반적인 투자 테제(Thesis)를 2~3문장으로 명확히 진술합니다.
       - 현재 가치 평가 대비 매수(Buy), 보유(Hold) 또는 매도(Sell) 의견과 적정 목표가(또는 상승 여력)에 대한 최종 결론을 1개의 문장으로 정리하십시오.

    출력되는 마크다운의 퀄리티가 매우 높아야 하며, 구글 검색을 통한 정확한 실시간 출처 정보를 기반으로 작성되어야 합니다.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=config
        )
        
        # 검색 출처 정보 추출 (google-genai SDK 스펙)
        sources = []
        try:
            metadata = response.candidates[0].grounding_metadata
            if metadata and metadata.grounding_chunks:
                for chunk in metadata.grounding_chunks:
                    web = chunk.web
                    if web:
                        sources.append(f"- [{web.title}]({web.uri})")
        except Exception:
            pass
            
        report_content = response.text
        
        if sources:
            report_content += "\n\n## 참고 및 실시간 뉴스 출처\n" + "\n".join(set(sources))
            
        return report_content
    except Exception as e:
        print(f"보고서 생성 중 오류 발생: {e}")
        return f"투자 보고서 생성 실패: {str(e)}"

def main():
    client = get_client()
    
    print("="*60)
    print("      실시간 뉴스 검색 및 주식 종합 투자 분석 보고서 생성기")
    print("="*60)
    
    stock_name = input("분석할 주식 종목명(예: 삼성전자, 애플, NVIDIA 등)을 입력하세요: ").strip()
    if not stock_name:
        print("종목명이 입력되지 않았습니다. 프로그램을 종료합니다.")
        return
        
    # 1. 티커 변환
    ticker = get_ticker_by_name(stock_name, client)
    if not ticker:
        print("올바른 티커를 찾지 못했습니다. 분석을 중단합니다.")
        return
        
    # 2. 최근 주가 변동 파악
    direction, pct_change, last_close = check_price_movement(ticker)
    print(f"-> 최근 변동: {direction} ({pct_change:+.2f}%), 종가: {last_close}")
    
    # 3. yfinance 재무 데이터 수집
    company_name, raw_financials, valuation_metrics = fetch_financial_data(ticker)
    
    # 4. 종합 보고서 작성 (Gemini)
    report = generate_report(
        stock_name=stock_name,
        ticker=ticker,
        direction=direction,
        pct_change=pct_change,
        last_close=last_close,
        company_name=company_name,
        raw_financials=raw_financials,
        client=client
    )
    
    # 5. 리포트 저장 및 출력
    import datetime
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    output_filename = f"{ticker.replace('.', '_')}_investment_report_{today_str}.md"
    output_path = os.path.join(os.getcwd(), output_filename)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print("\n" + "="*60)
        print(f"★ 보고서가 성공적으로 생성 및 저장되었습니다! ★")
        print(f"저장 경로: {output_path}")
        print("="*60 + "\n")
        
        # 화면에 주요 요약 내용 및 의견을 간략히 요약 출력
        print("--- [보고서 핵심 요약 및 의견] ---")
        lines = report.split('\n')
        summary_section = []
        capture = False
        count = 0
        for line in lines:
            if any(kw in line for kw in ["투자 테제", "최종 권장 사항", "요약", "투자 의견", "개요", "결론"]):
                capture = True
                count = 0
            if capture:
                print(line)
                count += 1
                if count > 15: # 각 섹션 최대 15줄 정도만 출력
                    capture = False
                    print("... (중략) ...")
        
    except Exception as e:
        print(f"보고서 파일 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
