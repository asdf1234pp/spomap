import React from "react";

function RegionList({ rankList, activeRegionId, onSelectRegion }) {
  if (!rankList || rankList.length === 0) {
    return (
      <div style={{ fontSize: 12, color: "#9ca3af" }}>데이터 없음</div>
    );
  }

  return (
    <>
      {rankList.map((item, idx) => {
        const isActive = item.region_id === activeRegionId;
        return (
          <div
            key={item.region_id}
            className={`rank-item ${isActive ? "active" : ""}`}
            onClick={() => onSelectRegion(item.region_id)}
          >
            <div className="rank-item-title">
              {idx + 1}. {item.region_name}
            </div>
            <div className="rank-item-sub">
              EDI: {item.edi.toFixed(1)} / Demand:{" "}
              {item.demand_score.toFixed(1)} / Supply:{" "}
              {item.supply_score.toFixed(1)}
            </div>
          </div>
        );
      })}
    </>
  );
}

export default RegionList;
