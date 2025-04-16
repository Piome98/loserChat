import React, { useState, useEffect } from 'react';

const MarketOverview = () => {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastFetchTime, setLastFetchTime] = useState(null);

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
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
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
      marginBottom: '1.5rem'
    },
    sectionTitle: {
      fontSize: '1rem',
      marginBottom: '0.75rem',
      fontWeight: '500',
      color: '#444'
    },
    grid: {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
      gap: '0.75rem'
    },
    item: {
      padding: '0.75rem',
      backgroundColor: '#f9f9f9',
      borderRadius: '4px',
      transition: 'transform 0.2s, box-shadow 0.2s'
    },
    itemName: {
      fontSize: '0.85rem',
      marginBottom: '0.25rem',
      color: '#555'
    },
    itemPrice: {
      fontWeight: 'bold',
      fontSize: '1.1rem',
      marginBottom: '0.25rem'
    },
    itemChangeUp: {
      color: '#4caf50',
      fontSize: '0.85rem',
      display: 'flex',
      alignItems: 'center'
    },
    itemChangeDown: {
      color: '#f44336',
      fontSize: '0.85rem',
      display: 'flex',
      alignItems: 'center'
    },
    noData: {
      padding: '2rem',
      textAlign: 'center',
      color: '#666',
      backgroundColor: '#f9f9f9',
      borderRadius: '4px'
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>시장 개요</h2>
        {lastFetchTime && <div style={styles.lastUpdated}>마지막 업데이트: {lastFetchTime}</div>}
      </div>
      
      {error && <div style={styles.error}>{error}</div>}
      
      {loading ? (
        <div style={styles.loading}>시장 데이터를 불러오는 중...</div>
      ) : (
        <div>
          {marketData ? (
            <>
              {/* 지수 섹션 */}
              {marketData.indices && marketData.indices.length > 0 && (
                <div style={styles.section}>
                  <h3 style={styles.sectionTitle}>주요 지수</h3>
                  <div style={styles.grid}>
                    {marketData.indices.map((item, index) => (
                      <div key={index} style={styles.item}>
                        <div style={styles.itemName}>{item.name}</div>
                        <div style={styles.itemPrice}>{item.price}</div>
                        <div style={item.status === 'up' ? styles.itemChangeUp : styles.itemChangeDown}>
                          {item.change} ({item.changePercent})
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* 환율 섹션 */}
              {marketData.currencies && marketData.currencies.length > 0 && (
                <div style={styles.section}>
                  <h3 style={styles.sectionTitle}>환율</h3>
                  <div style={styles.grid}>
                    {marketData.currencies.map((item, index) => (
                      <div key={index} style={styles.item}>
                        <div style={styles.itemName}>{item.name}</div>
                        <div style={styles.itemPrice}>{item.price}</div>
                        <div style={item.status === 'up' ? styles.itemChangeUp : styles.itemChangeDown}>
                          {item.change} ({item.changePercent})
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* 원자재 섹션 */}
              {marketData.commodities && marketData.commodities.length > 0 && (
                <div style={styles.section}>
                  <h3 style={styles.sectionTitle}>원자재</h3>
                  <div style={styles.grid}>
                    {marketData.commodities.map((item, index) => (
                      <div key={index} style={styles.item}>
                        <div style={styles.itemName}>{item.name}</div>
                        <div style={styles.itemPrice}>{item.price}</div>
                        <div style={item.status === 'up' ? styles.itemChangeUp : styles.itemChangeDown}>
                          {item.change} ({item.changePercent})
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {(!marketData.indices || marketData.indices.length === 0) && 
               (!marketData.currencies || marketData.currencies.length === 0) && 
               (!marketData.commodities || marketData.commodities.length === 0) && (
                <div style={styles.noData}>
                  현재 시장 데이터를 불러올 수 없습니다.<br />
                  잠시 후 다시 시도해 주세요.
                </div>
              )}
            </>
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
