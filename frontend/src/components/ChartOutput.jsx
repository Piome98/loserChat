import React, { useState, useEffect, memo } from 'react';
import axios from 'axios';
import ReactApexChart from 'react-apexcharts';

function ChartOutput({ selectedIndex = 'KOSPI' }) {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [indexName, setIndexName] = useState('코스피');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log(`차트 데이터 요청: ${selectedIndex}`);
        
        // 인증 토큰 가져오기 (필요한 경우)
        const token = localStorage.getItem('access_token');
        
        // API 요청 설정
        const config = {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          }
        };
        
        // API URL
        const url = `/api/crawling/daily-index-data/?code=${selectedIndex}&days=30`;
        console.log('API 요청 URL:', url);
        
        const response = await axios.get(url, config);
        console.log('API 응답:', response);
        
        // 응답 데이터 확인
        if (!response.data) {
          console.error('응답 데이터가 없습니다');
          setError('데이터를 불러올 수 없습니다');
          return;
        }
        
        console.log('응답 데이터:', response.data);
        
        // 데이터 필드 확인
        const responseData = response.data.data;
        if (!responseData || !Array.isArray(responseData) || responseData.length === 0) {
          console.error('유효한 데이터가 없습니다:', response.data);
          setError('유효한 데이터가 없습니다');
          return;
        }
        
        // 데이터 변환 (더 견고한 방식으로)
        const formattedData = [];
        for (const item of responseData) {
          if (!item || typeof item !== 'object') continue;
          
          let date = null;
          if (item.date) {
            try {
              // 날짜 포맷 처리
              date = new Date(item.date);
              if (isNaN(date.getTime())) {
                console.warn('유효하지 않은 날짜:', item.date);
                continue;
              }
            } catch (e) {
              console.warn('날짜 변환 오류:', e);
              continue;
            }
          } else {
            continue; // 날짜 없으면 건너뜀
          }
          
          let value = null;
          if (item.index_value !== undefined) {
            try {
              // 지수값 처리
              const valueStr = String(item.index_value).replace(/,/g, '');
              value = parseFloat(valueStr);
              if (isNaN(value)) {
                console.warn('유효하지 않은 지수값:', item.index_value);
                continue;
              }
            } catch (e) {
              console.warn('지수값 변환 오류:', e);
              continue;
            }
          } else {
            continue; // 지수값 없으면 건너뜀
          }
          
          // 유효한 데이터만 추가
          formattedData.push({
            x: date.getTime(),
            y: value
          });
        }
        
        if (formattedData.length === 0) {
          setError('차트 데이터를 생성할 수 없습니다');
          return;
        }
        
        // 날짜 순으로 정렬
        formattedData.sort((a, b) => a.x - b.x);
        
        console.log('변환된 차트 데이터:', formattedData);
        
        // 데이터 상태 업데이트
        setChartData(formattedData);
        setIndexName(response.data.name || selectedIndex);
        
      } catch (err) {
        console.error('차트 데이터 로딩 실패:', err);
        setError(`데이터를 불러오는 중 오류가 발생했습니다: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [selectedIndex]);

  const chartOptions = {
    chart: {
      type: 'area',
      height: 350,
      zoom: {
        enabled: true
      },
      toolbar: {
        show: true
      },
      background: '#fff'
    },
    dataLabels: {
      enabled: false
    },
    stroke: {
      curve: 'smooth',
      width: 2
    },
    title: {
      text: `${indexName} 일별 시세`,
      align: 'left',
      style: {
        fontSize: '16px',
        fontWeight: 'bold'
      }
    },
    grid: {
      borderColor: '#e7e7e7',
      row: {
        colors: ['#f3f3f3', 'transparent'],
        opacity: 0.5
      }
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.2,
        stops: [0, 100]
      }
    },
    xaxis: {
      type: 'datetime',
      labels: {
        datetimeFormatter: {
          year: 'yyyy',
          month: 'yyyy-MM',
          day: 'MM-dd'
        }
      }
    },
    yaxis: {
      labels: {
        formatter: (value) => { return value.toFixed(2) }
      },
      title: {
        text: '지수'
      }
    },
    tooltip: {
      x: {
        format: 'yyyy-MM-dd'
      }
    },
    theme: {
      mode: 'light',
      palette: 'palette1'
    }
  };

  const series = [{
    name: indexName,
    data: chartData
  }];

  return (
    <div className="chart-container">
      {loading ? (
        <div className="text-center my-4">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">로딩중...</span>
          </div>
          <p className="mt-2">데이터를 불러오는 중입니다...</p>
        </div>
      ) : error ? (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      ) : (
        <ReactApexChart
          options={chartOptions}
          series={series}
          type="area"
          height={350}
        />
      )}
    </div>
  );
}

export default memo(ChartOutput);
