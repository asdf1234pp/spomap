import React, { useEffect, useState, useMemo } from "react";
import {
  fetchSports,
  fetchRegions,
  fetchMetricsBySport,
  fetchRank,
} from "./api.js";
import MapView from "./components/MapView.jsx";
import Sidebar from "./components/Sidebar.jsx";
import LoadingOverlay from "./components/LoadingOverlay.jsx";

function App() {
  const [sports, setSports] = useState([]);
  const [selectedSport, setSelectedSport] = useState("");
  const [regions, setRegions] = useState([]);
  const [metrics, setMetrics] = useState([]);
  const [rankList, setRankList] = useState([]);
  const [activeRegionId, setActiveRegionId] = useState(null);
  const [loading, setLoading] = useState(true);

  // 초기: 스포츠 목록 + 지역 목록
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const [sportsData, regionsData] = await Promise.all([
          fetchSports(),
          fetchRegions(),
        ]);
        setSports(sportsData);
        setRegions(regionsData);
        if (sportsData.length > 0) {
          setSelectedSport(sportsData[0].code);
        }
      } catch (e) {
        console.error(e);
        alert("API 연결 오류 (백엔드 서버 실행 확인 필요)");
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  // 종목 선택 바뀔 때마다 메트릭 + 랭킹 불러오기
  useEffect(() => {
    if (!selectedSport) return;
    async function loadMetrics() {
      try {
        setLoading(true);
        const [metricData, rankData] = await Promise.all([
          fetchMetricsBySport(selectedSport),
          fetchRank(selectedSport, 10),
        ]);
        setMetrics(metricData);
        setRankList(rankData);
        if (rankData.length > 0) {
          setActiveRegionId(rankData[0].region_id);
        }
      } catch (e) {
        console.error(e);
        alert("메트릭 불러오기 실패");
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, [selectedSport]);

  const metricMap = useMemo(() => {
    const map = {};
    metrics.forEach((m) => {
      map[m.region_id] = m;
    });
    return map;
  }, [metrics]);

  const activeRegion = useMemo(() => {
    if (!activeRegionId) return null;
    const region = regions.find((r) => r.id === activeRegionId);
    const metric = metricMap[activeRegionId];
    if (!region || !metric) return null;
    return { region, metric };
  }, [activeRegionId, regions, metricMap]);

  return (
    <div className="app-root">
      <div className="sidebar">
        <Sidebar
          sports={sports}
          selectedSport={selectedSport}
          onChangeSport={setSelectedSport}
          rankList={rankList}
          activeRegionId={activeRegionId}
          onSelectRegion={setActiveRegionId}
          activeRegion={activeRegion}
        />
      </div>
      <div className="map-container">
        {loading && <LoadingOverlay text="데이터 로딩 중..." />}
        <MapView
          regions={regions}
          metricMap={metricMap}
          activeRegionId={activeRegionId}
          onSelectRegion={setActiveRegionId}
        />
      </div>
    </div>
  );
}

export default App;
