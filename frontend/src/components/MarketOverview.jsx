import React, { useState, useEffect, useRef } from 'react';

const MarketOverview = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetchTime, setLastFetchTime] = useState(null);
  const [activeTab, setActiveTab] = useState('domestic'); // 'domestic', 'international', 'currency', 'commodity'
  const [selectedItem, setSelectedItem] = useState(null);
  const chartRef = useRef(null);

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
      maxWidth: '100%'
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
    header: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: '1rem',
      paddingBottom: '0.5rem',
      borderBottom: '1px solid #eee'
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
      color: '#4caf50',
      fontSize: '0.85rem',
      display: 'flex',
      alignItems: 'center',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    },
    itemChangeDown: {
      color: '#f44336',
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
    tabs: {
      display: 'flex',
      marginBottom: '1rem',
      borderBottom: '1px solid #eee'
    },
    tab: {
      padding: '0.5rem 1rem',
      cursor: 'pointer',
      fontSize: '0.9rem',
      borderBottom: '2px solid transparent',
      transition: 'all 0.2s'
    },
    activeTab: {
      borderBottom: '2px solid #3f51b5',
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
      minHeight: '250px'
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
      height: '200px',
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
        boxShadow: item.status === 'up' ? '0 4px 6px rgba(0,128,0,0.1)' : 
                  item.status === 'down' ? '0 4px 6px rgba(255,0,0,0.1)' : 'none',
        ...(selectedItem && selectedItem.name === item.name ? styles.selectedItem : {})
      }}
      onClick={() => setSelectedItem(item)}
    >
      <div style={styles.itemName}>{item.name}</div>
      <div style={styles.itemPrice}>{item.price}</div>
      <div style={item.status === 'up' ? styles.itemChangeUp : styles.itemChangeDown}>
        {item.status === 'up' ? '▲' : item.status === 'down' ? '▼' : '■'} {item.change} ({item.changePercent})
      </div>
    </div>
  );

  // 차트 영역 렌더링 함수
  const renderChartSection = () => {
    if (!selectedItem) return null;
    
    return (
      <div style={styles.chartSection}>
        <div style={styles.chartTitle}>{selectedItem.name} 추이</div>
        <div style={styles.chartContainer} ref={chartRef}>
          <div style={{textAlign: 'center'}}>
            <div style={{fontSize: '1.2rem', fontWeight: 'bold', marginBottom: '10px'}}>{selectedItem.name}</div>
            <div style={{fontSize: '1.5rem', fontWeight: 'bold'}}>{selectedItem.price}</div>
            <div style={selectedItem.status === 'up' ? styles.itemChangeUp : styles.itemChangeDown}>
              {selectedItem.status === 'up' ? '▲' : selectedItem.status === 'down' ? '▼' : '■'} 
              {selectedItem.change} ({selectedItem.changePercent})
            </div>
            <div style={{marginTop: '20px', color: '#666'}}>
              실시간 차트 데이터 준비 중...
            </div>
          </div>
        </div>
      </div>
    );
  };

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
      </div>
    );
  };

  return (
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
  );
};

export default MarketOverview;
