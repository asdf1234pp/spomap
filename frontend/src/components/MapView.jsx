import React, { useMemo } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";

function MapView({ regions, metricMap, activeRegionId, onSelectRegion }) {
  const center = [36.5, 127.8]; // 한반도 대략 중앙

  const ediStats = useMemo(() => {
    const values = Object.values(metricMap).map((m) => m.edi);
    if (!values.length) return { min: 0, max: 0 };
    return {
      min: Math.min(...values),
      max: Math.max(...values),
    };
  }, [metricMap]);

  function getColor(edi) {
    if (ediStats.max === ediStats.min) {
      return "#38bdf8";
    }
    const t = (edi - ediStats.min) / (ediStats.max - ediStats.min);
    const r = Math.round(255 * t);
    const g = Math.round(120 * (1 - t));
    const b = Math.round(255 * (1 - t));
    return `rgb(${r},${g},${b})`;
  }

  function getRadius(edi) {
    if (!ediStats.max && !ediStats.min) return 10;
    const t = (edi - ediStats.min) / (ediStats.max - ediStats.min + 1e-6);
    return 8 + t * 18;
  }

  return (
    <>
      <MapContainer center={center} zoom={7} scrollWheelZoom={true}>
        <TileLayer
          attribution="&copy; OpenStreetMap"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {regions.map((r) => {
          const m = metricMap[r.id];
          if (!m) return null;
          const color = getColor(m.edi);
          const radius = getRadius(m.edi);
          const isActive = r.id === activeRegionId;
          return (
            <CircleMarker
              key={r.id}
              center={[r.lat, r.lng]}
              pathOptions={{
                color: isActive ? "#fbbf24" : color,
                fillColor: color,
                fillOpacity: 0.6,
                weight: isActive ? 3 : 1.5,
              }}
              radius={radius}
              eventHandlers={{
                click: () => onSelectRegion(r.id),
              }}
            >
              <Tooltip direction="top">
                <div style={{ fontSize: 12 }}>
                  <div style={{ fontWeight: 600 }}>{r.name}</div>
                  <div>EDI: {m.edi.toFixed(1)}</div>
                  <div>
                    Demand: {m.demand_score.toFixed(1)} / Supply:{" "}
                    {m.supply_score.toFixed(1)}
                  </div>
                </div>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
      <div className="legend">
        <div style={{ fontWeight: 600, marginBottom: 4 }}>
          운동 빈곤지수(EDI) 범례
        </div>
        <div style={{ fontSize: 12 }}>
          EDI = 수요점수 – 공급점수
          <br />
          값이 클수록 수요 대비 공급이 부족한 지역입니다.
        </div>
      </div>
    </>
  );
}

export default MapView;
