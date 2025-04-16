import axios from 'axios';

// API 인스턴스 생성
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 설정 - 인증 토큰 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 시장 개요 데이터 가져오기
export const getMarketOverview = async () => {
  try {
    const response = await api.get('/crawling/market-overview/');
    return response.data;
  } catch (error) {
    console.error('시장 개요 데이터 가져오기 오류:', error);
    // 오류 발생 시 더미 데이터 반환
    return {
      updateTime: new Date().toLocaleString(),
      indices: [
        {
          name: 'KOSPI',
          price: '2,778.30',
          change: '+12.90',
          changePercent: '+0.47%'
        },
        {
          name: 'KOSDAQ',
          price: '905.68',
          change: '+10.50',
          changePercent: '+1.17%'
        },
        {
          name: '다우존스',
          price: '38,797.40',
          change: '-32.17',
          changePercent: '-0.08%'
        },
        {
          name: '나스닥',
          price: '15,982.04',
          change: '+7.74',
          changePercent: '+0.05%'
        },
        {
          name: '상하이종합',
          price: '3,113.95',
          change: '+34.37',
          changePercent: '+1.12%'
        }
      ],
      currencies: [
        {
          name: '원/달러',
          price: '1,328.50',
          change: '-8.20',
          changePercent: '-0.61%'
        },
        {
          name: '원/엔',
          price: '881.53',
          change: '+3.47',
          changePercent: '+0.40%'
        },
        {
          name: '국고채 3년',
          price: '3.387%',
          change: '+0.012',
          changePercent: '+0.36%'
        }
      ]
    };
  }
};

// 뉴스 데이터 가져오기
export const getNews = async (stockSymbol = null, category = null) => {
  try {
    const params = {};
    if (stockSymbol) params.symbol = stockSymbol;
    if (category) params.category = category;
    
    const response = await api.get('/crawling/market-news/', { params });
    return response.data;
  } catch (error) {
    console.error('뉴스 데이터 가져오기 오류:', error);
    
    // 현재 날짜 구하기
    const today = new Date();
    const formattedToday = today.toLocaleDateString();
    const yesterday = new Date(today);
    yesterday.setDate(today.getDate() - 1);
    const formattedYesterday = yesterday.toLocaleDateString();
    
    // 더미 뉴스 데이터
    const allNews = [
      {
        id: 1,
        title: '삼성전자, 신규 AI 반도체 양산 본격화... 5나노 기반',
        summary: '삼성전자가 5나노 기술 기반의 AI 반도체 양산을 본격화한다고 밝혔다. 이번 신규 반도체는 글로벌 AI 시장 공략을 위한 전략적 제품으로...',
        source: '한국경제',
        date: formattedToday,
        url: 'https://example.com/news/samsung-ai-chip',
        category: '기업',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: ['005930']
      },
      {
        id: 2,
        title: '원/달러 환율, 1330원 붕괴... "중국발 경기 우려에 영향"',
        summary: '원/달러 환율이 1330원 선이 무너졌다. 전문가들은 중국 경기둔화 우려와 미국 경제지표 호조로 인한 달러 강세가 원인이라고 분석...',
        source: '연합인포맥스',
        date: formattedToday,
        url: 'https://example.com/news/won-dollar-rate',
        category: '경제',
        imageUrl: null,
        relatedSymbols: []
      },
      {
        id: 3,
        title: 'LG화학-포스코, 배터리 소재 합작법인 설립 추진',
        summary: 'LG화학과 포스코가 배터리 소재 생산을 위한 합작법인 설립을 추진한다. 양사는 글로벌 전기차 시장 확대에 대응하기 위해...',
        source: '매일경제',
        date: formattedYesterday,
        url: 'https://example.com/news/lg-posco-joint-venture',
        category: '기업',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: ['051910', '005490']
      },
      {
        id: 4,
        title: '연준 "5월 금리인하 가능성 낮아"... 인플레이션 우려',
        summary: '미 연방준비제도(Fed)가 5월 금리인하 가능성이 낮다고 시사했다. 인플레이션이 예상보다 둔화되지 않아 추가 관찰이 필요하다는 입장...',
        source: '로이터',
        date: formattedYesterday,
        url: 'https://example.com/news/fed-rate-cut',
        category: '국제',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: []
      },
      {
        id: 5,
        title: '현대차-기아, 미 IRA 세제 혜택 잠정 적용... 전기차 경쟁력 제고',
        summary: '현대차와 기아가 미국 인플레이션 감축법(IRA)에 따른 세제 혜택을 잠정 적용받게 됐다. 이로써 양사의 미국 내 전기차 판매에 강력한 경쟁력을...',
        source: '아시아경제',
        date: formattedYesterday,
        url: 'https://example.com/news/hyundai-kia-ira',
        category: '기업',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: ['005380', '000270']
      },
      {
        id: 6,
        title: '반도체주 강세... 엔비디아 실적 호조에 국내주 동반 상승',
        summary: '엔비디아의 실적 호조에 힘입어 국내 반도체 관련주들이 강세를 보이고 있다. 삼성전자와 SK하이닉스 등 메모리 반도체주뿐 아니라...',
        source: '이데일리',
        date: formattedToday,
        url: 'https://example.com/news/semiconductor-stocks',
        category: '증시',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: ['005930', '000660']
      },
      {
        id: 7,
        title: `美中 긴장 완화 움직임... 블링컨-왕이 '외교 채널' 가동`,
        summary: `미국과 중국의 긴장 관계가 완화되는 조짐이 보이고 있다. 토니 블링컨 미 국무장관과 왕이 중국 외교부장이 직접 대화 채널을 가동하며...`,
        source: '뉴시스',
        date: formattedToday,
        url: 'https://example.com/news/us-china-relations',
        category: '국제',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: []
      },
      {
        id: 8,
        title: 'KOSPI, 외국인 순매수에 상승... 바이오·2차전지주 강세',
        summary: '코스피 지수가 외국인 투자자들의 순매수에 상승세를 보였다. 특히 바이오 및 2차전지 관련주들이 강세를 보이며 지수 상승을 이끌었다...',
        source: '한국경제TV',
        date: formattedToday,
        url: 'https://example.com/news/kospi-foreign-investors',
        category: '증시',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: []
      },
      {
        id: 9,
        title: '한국은행, 기준금리 동결... "인플레이션 우려 여전"',
        summary: '한국은행 금융통화위원회가 기준금리를 현 수준에서 동결했다. 최근 물가상승세가 완화되고 있으나 불확실성이 여전히 높다는 판단에...',
        source: '머니투데이',
        date: formattedYesterday,
        url: 'https://example.com/news/bok-rate',
        category: '경제',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: []
      },
      {
        id: 10,
        title: '대규모 실적 호조에 네이버 주가 급등... 클라우드·AI 사업 성장 기대감',
        summary: '네이버가 예상을 뛰어넘는 실적을 발표해 주가가 급등했다. 특히 클라우드와 AI 사업 부문의 높은 성장세가 주목받으며 미래 성장동력으로...',
        source: '서울경제',
        date: formattedToday,
        url: 'https://example.com/news/naver-stock-jump',
        category: '기업',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: ['035420']
      },
      {
        id: 11,
        title: '유럽중앙은행(ECB), 금리 인하 시그널... "6월 가능성 높아"',
        summary: '유럽중앙은행(ECB)이 6월 금리 인하를 시사했다. 유로존의 인플레이션이 목표치에 가까워지면서 긴축 완화에 대한 기대감이 높아지고 있다...',
        source: '블룸버그',
        date: formattedToday,
        url: 'https://example.com/news/ecb-rate-cut',
        category: '국제',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: []
      },
      {
        id: 12,
        title: '미국 1분기 GDP 예상 하회... 경기 둔화 우려 확산',
        summary: '미국의 1분기 국내총생산(GDP) 성장률이 시장 예상치를 하회했다. 이에 따라 세계 최대 경제국의 경기 둔화 우려가 확산되며 글로벌 시장에...',
        source: 'CNBC',
        date: formattedYesterday,
        url: 'https://example.com/news/us-gdp-q1',
        category: '국제',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: []
      },
      {
        id: 13,
        title: '삼성바이오로직스, 글로벌 제약사와 5조원 규모 CDMO 계약 체결',
        summary: '삼성바이오로직스가 글로벌 대형 제약사와 5조원 규모의 바이오의약품 위탁개발생산(CDMO) 계약을 체결했다고 발표했다. 이번 계약으로...',
        source: '파이낸셜뉴스',
        date: formattedToday,
        url: 'https://example.com/news/samsung-biologics-contract',
        category: '기업',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: ['207940']
      },
      {
        id: 14,
        title: '금융위, 가상자산 거래소 관리·감독 강화 방침... "투자자 보호 최우선"',
        summary: '금융위원회가 가상자산 거래소에 대한 관리·감독을 강화하겠다는 방침을 밝혔다. 최근 가상자산 시장의 변동성이 확대되면서 투자자 보호의...',
        source: '디지털타임스',
        date: formattedYesterday,
        url: 'https://example.com/news/crypto-regulation',
        category: '경제',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: []
      },
      {
        id: 15,
        title: '세계 주요 IT기업 실적시즌... 빅테크 성적표 주목',
        summary: '세계 주요 IT 기업들의 실적 발표 시즌이 시작됐다. 마이크로소프트, 구글, 애플 등 빅테크 기업들의 성적표에 글로벌 증시가 주목하고 있다...',
        source: '전자신문',
        date: formattedToday,
        url: 'https://example.com/news/bigtech-earnings',
        category: '국제',
        imageUrl: 'https://via.placeholder.com/150',
        relatedSymbols: []
      }
    ];
    
    if (stockSymbol) {
      // 특정 종목 관련 뉴스만 필터링
      return allNews.filter(news => news.relatedSymbols.includes(stockSymbol));
    } else if (category) {
      // 특정 카테고리 뉴스만 필터링
      return allNews.filter(news => news.category === category);
    } else {
      // 전체 뉴스 반환
      return allNews;
    }
  }
};

// 카테고리별 뉴스 가져오기 함수들
export const getEconomyNews = async (count = 15) => {
  const news = await getNews(null, '경제');
  return news.slice(0, count);
};

export const getCorporateNews = async (count = 15) => {
  const news = await getNews(null, '기업');
  return news.slice(0, count);
};

export const getMarketNews = async (count = 15) => {
  const news = await getNews(null, '증시');
  return news.slice(0, count);
};

export const getInternationalNews = async (count = 15) => {
  const news = await getNews(null, '국제');
  return news.slice(0, count);
};

// 최신 뉴스 가져오기 (모든 카테고리에서 최신 n개)
export const getLatestNews = async (count = 5) => {
  try {
    const allNews = await getNews();
    // 날짜순으로 정렬
    return allNews
      .sort((a, b) => new Date(b.date) - new Date(a.date))
      .slice(0, count);
  } catch (error) {
    console.error('최신 뉴스 가져오기 오류:', error);
    return [];
  }
};

// 인베스팅닷컴 위젯 대체용 뉴스 컴포넌트 생성 함수
export const createNewsComponent = (container, category = '경제', title = '경제 뉴스', count = 15) => {
  if (!container) return;

  // 인베스팅닷컴 위젯 대신 표시할 HTML
  container.innerHTML = `
    <div class="custom-news-widget">
      <div class="widget-header">
        <h3>${title}</h3>
        <small>${new Date().toLocaleDateString()} 기준</small>
      </div>
      <div class="news-list-container">
        <div class="loading">로딩 중...</div>
      </div>
    </div>
  `;
  
  // 스타일 추가
  const style = document.createElement('style');
  style.textContent = `
    .custom-news-widget {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
      overflow: hidden;
    }
    .widget-header {
      background-color: #f8f9fa;
      padding: 10px 15px;
      border-bottom: 1px solid #e0e0e0;
    }
    .widget-header h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }
    .widget-header small {
      color: #888;
      font-size: 12px;
    }
    .news-list-container {
      padding: 0;
    }
    .loading {
      padding: 20px;
      text-align: center;
      color: #888;
    }
    .news-item {
      padding: 10px 15px;
      border-bottom: 1px solid #f0f0f0;
    }
    .news-item:last-child {
      border-bottom: none;
    }
    .news-item a {
      color: #333;
      text-decoration: none;
      font-weight: 500;
      font-size: 14px;
      line-height: 1.4;
      display: block;
      margin-bottom: 5px;
    }
    .news-item a:hover {
      color: #0056b3;
    }
    .news-item .source-date {
      font-size: 11px;
      color: #888;
      display: flex;
      justify-content: space-between;
    }
  `;
  document.head.appendChild(style);
  
  // 뉴스 데이터 가져와서 표시
  const newsContainer = container.querySelector('.news-list-container');
  getNews(null, category)
    .then(news => {
      if (news && news.length > 0) {
        const newsItems = news.slice(0, count).map(item => `
          <div class="news-item">
            <a href="${item.url}" target="_blank">${item.title}</a>
            <div class="source-date">
              <span>${item.source}</span>
              <span>${item.date}</span>
            </div>
          </div>
        `).join('');
        
        newsContainer.innerHTML = newsItems;
      } else {
        newsContainer.innerHTML = '<div class="loading">뉴스를 불러올 수 없습니다.</div>';
      }
    })
    .catch(error => {
      console.error('뉴스 위젯 로드 오류:', error);
      newsContainer.innerHTML = '<div class="loading">뉴스를 불러올 수 없습니다.</div>';
    });
};

// 기존 인베스팅닷컴 위젯을 대체하는 함수
export const replaceInvestingWidgets = () => {
  // 기존 위젯 스크립트 제거
  const scripts = document.querySelectorAll('script[src*="widgets.investing.com"]');
  scripts.forEach(script => {
    script.remove();
  });
  
  // 위젯 컨테이너 찾기
  const containers = document.querySelectorAll('.investing-news-widget');
  
  // 각 컨테이너를 커스텀 뉴스 컴포넌트로 대체
  containers.forEach(container => {
    // 컨테이너에서 카테고리와 제목 속성 가져오기
    const category = container.getAttribute('data-category') || '경제';
    const title = container.getAttribute('data-title') || '경제 뉴스';
    const count = parseInt(container.getAttribute('data-count') || '15', 10);
    
    // 커스텀 뉴스 컴포넌트 생성
    createNewsComponent(container, category, title, count);
  });
};

// 페이지 로드 시 인베스팅 위젯 대체 함수
window.addEventListener('DOMContentLoaded', () => {
  // 약간의 지연 후 위젯 대체 실행 (기존 위젯이 로드될 시간 부여)
  setTimeout(replaceInvestingWidgets, 1000);
});

export default {
  getMarketOverview,
  getNews,
  getEconomyNews,
  getCorporateNews,
  getMarketNews,
  getInternationalNews,
  getLatestNews,
  createNewsComponent,
  replaceInvestingWidgets
};