import React, { useState, useEffect, useCallback } from 'react';
import ChartOutput from './ChartOutput';

// 시장 항목을 API 코드로 매핑하는 객체
const marketNameToCodeMap = {
  // 국내 지수
  '코스피': 'KOSPI',
  '코스닥': 'KOSDAQ',
  '코스피 200': 'KPI200',
  
  // 해외 지수
  '다우': 'DJI',
  '다우존스': 'DJI',
  '나스닥': 'NASDAQ',
  'S&P 500': 'SP500',
  'S&P': 'SP500',
  
  // 원자재
  'WTI': 'WTI',
  '금': 'GOLD',
  '은': 'SILVER',
  
  // 환율
  '달러/원': 'USD/KRW',
  '엔/원': 'JPY/KRW',
  '유로/원': 'EUR/KRW'
};

const MarketOverview = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetchTime, setLastFetchTime] = useState(null);
  const [activeTab, setActiveTab] = useState('domestic'); // 'domestic', 'international', 'currency', 'commodity'
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedCode, setSelectedCode] = useState('KOSPI'); // 기본값은 코스피

  // API 호출 함수
  const fetchMarketData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 인증 토큰 가져오기
      const token = localStorage.getItem('access_token');
      
      // 백엔드 API 호출 - 전체 URL로 요청 (URL 수정)
      const response = await fetch('http://localhost:8000/api/crawling/naver-finance-market/', {
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log("시장 데이터 응답:", data);
      
      // 데이터 구조 상세 분석을 위한 로깅 추가
      console.log("시장 데이터 타입:", typeof data);
      console.log("시장 데이터 구조:", Object.keys(data));
      console.log("인덱스 항목 타입:", Array.isArray(data.indices) ? "배열" : typeof data.indices);
      console.log("인덱스 항목 개수:", data.indices?.length || 0);
      console.log("통화 항목 타입:", Array.isArray(data.currencies) ? "배열" : typeof data.currencies);
      console.log("통화 항목 개수:", data.currencies?.length || 0);
      console.log("원자재 항목 타입:", Array.isArray(data.commodities) ? "배열" : typeof data.commodities);
      console.log("원자재 항목 개수:", data.commodities?.length || 0);
      
      // 환율 항목 자세히 로깅
      console.log("환율 항목 상세:", data.currencies);
      
      setMarketData(data);
      setLastFetchTime(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("시장 데이터 로드 오류:", error);
      setError(`시장 데이터를 불러올 수 없습니다: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 항목을 선택했을 때 호출되는 함수
  const handleItemSelect = (item) => {
    setSelectedItem(item);
    
    // 항목 이름에서 코드 추출
    const name = item.name.replace('...', ''); // 말줄임표 제거
    
    // 이름으로 코드 매핑
    let code = 'KOSPI'; // 기본값
    
    // 정확한 매핑 시도
    for (const [itemName, itemCode] of Object.entries(marketNameToCodeMap)) {
      if (name.includes(itemName)) {
        code = itemCode;
        break;
      }
    }
    
    // 유사 매핑 시도 (정확한 매칭이 없을 경우)
    if (code === 'KOSPI' && name !== '코스피') {
      if (name.toLowerCase().includes('kosdaq') || name.includes('코스닥')) {
        code = 'KOSDAQ';
      } else if (name.toLowerCase().includes('dow') || name.includes('다우')) {
        code = 'DJI';
      } else if (name.toLowerCase().includes('nasdaq') || name.includes('나스닥')) {
        code = 'NASDAQ';
      } else if (name.toLowerCase().includes('s&p') || name.includes('S&P')) {
        code = 'SP500';
      } else if (name.toLowerCase().includes('wti') || name.includes('원유')) {
        code = 'WTI';
      } else if (name.toLowerCase().includes('gold') || name.includes('금')) {
        code = 'GOLD';
      } else if (name.toLowerCase().includes('silver') || name.includes('은')) {
        code = 'SILVER';
      } else if (name.toLowerCase().includes('usd') || name.includes('달러')) {
        code = 'USD/KRW';
      } else if (name.toLowerCase().includes('jpy') || name.includes('엔')) {
        code = 'JPY/KRW';
      } else if (name.toLowerCase().includes('eur') || name.includes('유로')) {
        code = 'EUR/KRW';
      }
    }
    
    console.log(`선택된 항목: ${name}, 코드: ${code}`);
    setSelectedCode(code);
  };

  // 차트 렌더링 함수
  const renderChartSection = useCallback(() => {
    return (
      <div style={{
        padding: '1rem',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        marginTop: '1rem',
        marginBottom: '2rem',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexDirection: 'column',
        width: '100%',
        minHeight: '300px'
      }}>
        {selectedItem ? (
          <div style={{ width: '100%' }}>
            <h3 style={{ textAlign: 'center', marginBottom: '1rem' }}>
              {selectedItem.name} 차트
            </h3>
            <ChartOutput selectedIndex={selectedCode} />
          </div>
        ) : (
          <div style={{ textAlign: 'center', color: '#666', paddingBottom: '2rem', paddingTop: '2rem', width: '100%', minHeight: '250px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <p>항목을 선택하여 차트를 표시합니다.</p>
          </div>
        )}
      </div>
    );
  }, [selectedItem, selectedCode]);

  // 컴포넌트 마운트 시 한 번만 실행
  useEffect(() => {
    fetchMarketData();
    
    const intervalId = setInterval(() => {
      fetchMarketData();
    }, 300000); // 5분마다 갱신
    
    return () => clearInterval(intervalId);
  }, []);

  // 인라인 스타일 객체
  const styles = {
    container: {
      marginBottom: '1.5rem',
      backgroundColor: '#fff',
      borderRadius: '8px',
      padding: '1rem',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      width: '100%',
      maxWidth: '100%',
      height: 'auto',
      position: 'relative',
      display: 'flex',
      flexDirection: 'column'
    },
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '1rem',
      paddingBottom: '0.5rem',
      borderBottom: '1px solid #eee',
      backgroundColor: '#fff',
      zIndex: 10
    },
    tabs: {
      display: 'flex',
      marginBottom: '1rem',
      borderBottom: '1px solid #eee',
      backgroundColor: '#fff',
      zIndex: 9,
      paddingTop: '0.5rem'
    },
    scrollContent: {
      flexGrow: 1,
      width: '100%',
      display: 'flex',
      flexDirection: 'column',
      overflowY: 'auto',
      maxHeight: '700px',
      scrollbarWidth: 'thin',
      scrollbarColor: '#3f51b5 #f5f5f5'
    },
    contentContainer: {
      display: 'flex',
      flexDirection: 'column',
      gap: '1rem',
      width: '100%'
    },
    tabContent: {
      minHeight: '250px',
      width: '100%'
    },
    gridContainer: {
      width: '100%'
    },
    title: {
      margin: '0',
      fontSize: '1.25rem',
      fontWeight: '600'
    },
    lastUpdated: {
      fontSize: '0.8rem',
      color: '#666'
    },
    error: {
      color: '#d32f2f',
      padding: '1rem',
      textAlign: 'center',
      backgroundColor: 'rgba(211, 47, 47, 0.1)',
      borderRadius: '4px',
      margin: '1rem 0'
    },
    loading: {
      padding: '2rem',
      textAlign: 'center',
      color: '#666'
    },
    section: {
      marginBottom: '1.5rem',
      width: '100%'
    },
    sectionTitle: {
      fontSize: '1rem',
      marginBottom: '0.75rem',
      fontWeight: '500',
      color: '#444'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: '0.75rem',
      width: '100%'
    },
    item: {
      padding: '0.75rem',
      backgroundColor: '#f9f9f9',
      borderRadius: '4px',
      transition: 'transform 0.2s, box-shadow 0.2s',
      cursor: 'pointer',
      width: '100%',
      height: '100px',
      minHeight: '100px',
      maxHeight: '100px',
      boxSizing: 'border-box',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'space-between',
      overflow: 'hidden'
    },
    selectedItem: {
      border: '2px solid #3f51b5',
      backgroundColor: '#e8eaf6'
    },
    itemName: {
      fontSize: '0.85rem',
      marginBottom: '0.25rem',
      color: '#555',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      width: '100%'
    },
    itemPrice: {
      fontWeight: 'bold',
      fontSize: '1.1rem',
      marginBottom: '0.25rem',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    },
    itemChangeUp: {
      color: '#f44336',
      fontSize: '0.85rem',
      display: 'flex',
      alignItems: 'center',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    },
    itemChangeDown: {
      color: '#2196f3',
      fontSize: '0.85rem',
      display: 'flex',
      alignItems: 'center',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    },
    noData: {
      padding: '2rem',
      textAlign: 'center',
      color: '#666',
      backgroundColor: '#f9f9f9',
      borderRadius: '4px'
    },
    tab: {
      padding: '0.5rem 1rem',
      cursor: 'pointer',
      fontSize: '0.9rem',
      borderBottom: '2px solid transparent',
      transition: 'all 0.2s'
    },
    activeTab: {
      borderBottom: '2px solid rgb(0, 38, 255)',
      color: '#3f51b5',
      fontWeight: '500'
    },
    inactiveTab: {
      color: '#777',
      '&:hover': {
        color: '#3f51b5'
      }
    },
    refreshButton: {
      backgroundColor: '#f5f5f5',
      border: 'none',
      borderRadius: '4px',
      padding: '0.3rem 0.6rem',
      fontSize: '0.8rem',
      cursor: 'pointer',
      marginLeft: '0.5rem',
      '&:hover': {
        backgroundColor: '#e0e0e0'
      }
    },
    chartSection: {
      padding: '1rem',
      backgroundColor: '#f5f5f5',
      borderRadius: '8px',
      marginTop: '1rem',
      minHeight: '300px'
    },
    chartTitle: {
      fontSize: '1rem',
      fontWeight: '500',
      marginBottom: '0.5rem',
      textAlign: 'center'
    },
    noChartData: {
      color: '#666',
      fontSize: '0.9rem',
      textAlign: 'center',
      padding: '2rem'
    },
    chartContainer: {
      width: '100%',
      height: '350px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  };

  // 국내 지수 필터링 및 표준화
  const domesticIndices = marketData?.indices?.filter(item => 
    item.name.toLowerCase().includes('kospi') || 
    item.name.toLowerCase().includes('kosdaq')
  ).map(item => ({
    ...item,
    name: item.name.length > 10 ? item.name.substring(0, 10) + '...' : item.name, // 이름 길이 제한
    price: item.price.toString().length > 8 ? item.price.toString().substring(0, 8) : item.price, // 가격 길이 제한
    change: item.change.toString().length > 6 ? item.change.toString().substring(0, 6) : item.change, // 변화량 길이 제한
    changePercent: item.changePercent.toString().length > 6 ? item.changePercent.toString().substring(0, 6) : item.changePercent // 변화율 길이 제한
  })) || [];

  // 해외 지수 필터링 및 표준화
  const internationalIndices = marketData?.indices?.filter(item => {
    const name = item.name.toLowerCase();
    return name.includes('다우존스') || 
           name.includes('나스닥') || 
           name.includes('s&p') || 
           name.includes('항셍');
  }).map(item => ({
    ...item,
    name: item.name.length > 10 ? item.name.substring(0, 10) + '...' : item.name,
    price: item.price.toString().length > 8 ? item.price.toString().substring(0, 8) : item.price,
    change: item.change.toString().length > 6 ? item.change.toString().substring(0, 6) : item.change,
    changePercent: item.changePercent.toString().length > 6 ? item.changePercent.toString().substring(0, 6) : item.changePercent
  })) || [];

  // 환율 데이터 표준화
  const currencies = (marketData?.currencies || []).map(item => ({
    ...item,
    name: item.name.length > 10 ? item.name.substring(0, 10) + '...' : item.name,
    price: item.price.toString().length > 8 ? item.price.toString().substring(0, 8) : item.price,
    change: item.change.toString().length > 6 ? item.change.toString().substring(0, 6) : item.change,
    changePercent: item.changePercent.toString().length > 6 ? item.changePercent.toString().substring(0, 6) : item.changePercent
  }));

  // 원자재 데이터 표준화
  const commodities = (marketData?.commodities || []).map(item => ({
    ...item,
    name: item.name.length > 10 ? item.name.substring(0, 10) + '...' : item.name,
    price: item.price.toString().length > 8 ? item.price.toString().substring(0, 8) : item.price,
    change: item.change.toString().length > 6 ? item.change.toString().substring(0, 6) : item.change,
    changePercent: item.changePercent.toString().length > 6 ? item.changePercent.toString().substring(0, 6) : item.changePercent
  }));

  // 개별 시장 항목 렌더링 함수
  const renderMarketItem = (item, index) => (
    <div 
      key={index} 
      style={{
        ...styles.item,
        transform: item.status === 'up' ? 'translateY(-2px)' : 'none',
        boxShadow: item.status === 'up' ? '0 4px 6px rgba(244,67,54,0.1)' : 
                  item.status === 'down' ? '0 4px 6px rgba(33,150,243,0.1)' : 'none',
        ...(selectedItem && selectedItem.name === item.name ? styles.selectedItem : {})
      }}
      onClick={() => handleItemSelect(item)}
    >
      <div style={styles.itemName}>{item.name}</div>
      <div style={styles.itemPrice}>{item.price}</div>
      <div style={item.status === 'up' ? styles.itemChangeUp : styles.itemChangeDown}>
        {item.status === 'up' ? '▲' : item.status === 'down' ? '▼' : '■'} {item.change} ({item.changePercent})
      </div>
    </div>
  );

  // 현재 활성화된 탭에 따라 데이터 표시
  const renderActiveTabContent = () => {
    let title = '';
    let items = [];
    
    switch(activeTab) {
      case 'domestic':
        title = '국내 지수';
        items = domesticIndices;
        break;
      case 'international':
        title = '해외 지수';
        items = internationalIndices;
        break;
      case 'currency':
        title = '환율';
        items = currencies;
        break;
      case 'commodity':
        title = '원자재';
        items = commodities;
        break;
      default:
        return null;
    }
    
    // 항상 짝수 개의 항목을 표시하기 위해 빈 항목 추가
    const displayItems = [...items];
    const itemCount = Math.max(4, Math.ceil(items.length / 2) * 2); // 최소 4개(2행) 이상 항목 표시
    
    for (let i = items.length; i < itemCount; i++) {
      displayItems.push({ empty: true, id: `empty-${i}` });
    }
    
    return (
      <div style={styles.contentContainer}>
        <div style={styles.tabContent}>
          <h3 style={styles.sectionTitle}>{title}</h3>
          {items.length > 0 ? (
            <div style={styles.gridContainer}>
              <div style={styles.grid}>
                {displayItems.map((item, index) => item.empty ? 
                  <div key={`empty-${index}`} style={{...styles.item, visibility: 'hidden', boxShadow: 'none'}}></div> : 
                  renderMarketItem(item, index)
                )}
              </div>
            </div>
          ) : (
            <div style={styles.noData}>{title} 데이터를 불러올 수 없습니다.</div>
          )}
        </div>
        {renderChartSection()}
        <div style={{ height: '50px' }}></div> {/* 추가 빈 공간 */}
      </div>
    );
  };

  return (
    <>
      <style>
        {`
          .market-data-scrollable::-webkit-scrollbar {
            width: 8px;
          }
          .market-data-scrollable::-webkit-scrollbar-track {
            background: #f5f5f5;
          }
          .market-data-scrollable::-webkit-scrollbar-thumb {
            background-color: #3f51b5;
            border-radius: 4px;
          }
        `}
      </style>
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>시장 개요</h2>
        <div style={{display: 'flex', alignItems: 'center'}}>
          {lastFetchTime && <div style={styles.lastUpdated}>마지막 업데이트: {lastFetchTime}</div>}
          <button 
            onClick={fetchMarketData} 
            style={{...styles.refreshButton, marginLeft: '0.5rem'}}
            disabled={loading}
          >
            {loading ? '로딩 중...' : '새로고침'}
          </button>
        </div>
      </div>
      
      {/* 탭 네비게이션 */}
      <div style={styles.tabs}>
        <div 
          style={{...styles.tab, ...(activeTab === 'domestic' ? styles.activeTab : styles.inactiveTab)}}
            onClick={() => {setActiveTab('domestic'); setSelectedItem(null);}}
        >
          국내 지수
        </div>
        <div 
          style={{...styles.tab, ...(activeTab === 'international' ? styles.activeTab : styles.inactiveTab)}}
            onClick={() => {setActiveTab('international'); setSelectedItem(null);}}
        >
          해외 지수
        </div>
        <div 
          style={{...styles.tab, ...(activeTab === 'currency' ? styles.activeTab : styles.inactiveTab)}}
            onClick={() => {setActiveTab('currency'); setSelectedItem(null);}}
        >
          환율
        </div>
        <div 
          style={{...styles.tab, ...(activeTab === 'commodity' ? styles.activeTab : styles.inactiveTab)}}
            onClick={() => {setActiveTab('commodity'); setSelectedItem(null);}}
        >
          원자재
        </div>
      </div>
      
      {error && <div style={styles.error}>{error}</div>}
      
        <div style={styles.scrollContent} className="market-data-scrollable">
      {loading ? (
        <div style={styles.loading}>시장 데이터를 불러오는 중...</div>
      ) : (
        <div>
          {marketData ? (
            renderActiveTabContent()
          ) : (
            <div style={styles.noData}>
              현재 시장 데이터를 불러올 수 없습니다.<br />
              잠시 후 다시 시도해 주세요.
            </div>
          )}
        </div>
      )}
    </div>
      </div>
    </>
  );
};

export default MarketOverview;
