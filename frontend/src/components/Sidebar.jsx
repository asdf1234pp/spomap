import React from "react";
import RegionList from "./RegionList.jsx";

function Sidebar({
  sports,
  selectedSport,
  onChangeSport,
  rankList,
  activeRegionId,
  onSelectRegion,
  activeRegion,
}) {
  return (
    <div>
      <h1>SpoMap</h1>
      <div style={{ fontSize: 12, color: "#9ca3af", marginBottom: 8 }}>
        생활체육 수요·공급 격차 인사이트
      </div>

      <h2>종목 카테고리</h2>
      <select
        value={selectedSport}
        onChange={(e) => onChangeSport(e.target.value)}
      >
        {sports.map((sp) => (
          <option key={sp.code} value={sp.code}>
            {sp.label}
          </option>
        ))}
      </select>

      <div className="summary-box">
        <div style={{ fontWeight: 600, marginBottom: 6 }}>선택 지역 요약</div>
        {activeRegion ? (
          <>
            <div style={{ marginBottom: 4 }}>{activeRegion.region.name}</div>
            <div style={{ fontSize: 12 }}>
              DemandScore: {activeRegion.metric.demand_score.toFixed(1)}
              <br />
              SupplyScore: {activeRegion.metric.supply_score.toFixed(1)}
              <br />
              EDI (운동 빈곤지수):{" "}
              <span style={{ color: "#38bdf8" }}>
                {activeRegion.metric.edi.toFixed(1)}
              </span>
            </div>
            <div
              style={{
                marginTop: 6,
                fontSize: 11,
                color: "#9ca3af",
                lineHeight: 1.4,
              }}
            >
              EDI = 수요점수 – 공급점수 입니다.
              값이 클수록 수요 대비 공급이 부족한 지역(인프라 취약)입니다.
            </div>
          </>
        ) : (
          <div style={{ fontSize: 12, color: "#9ca3af" }}>
            왼쪽 리스트 또는 지도를 클릭해서 지역을 선택하세요.
          </div>
        )}
      </div>

      <h2>운동 빈곤지수 상위 지역</h2>
      <div className="rank-list">
        <RegionList
          rankList={rankList}
          activeRegionId={activeRegionId}
          onSelectRegion={onSelectRegion}
        />
      </div>
    </div>
  );
}

export default Sidebar;
