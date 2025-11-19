import axios from "axios";

// 로컬 개발용 기본값
const API_BASE =
  import.meta.env.VITE_API_BASE || "http://localhost:8000";


export async function fetchSports() {
  const res = await axios.get(`${API_BASE}/api/sports`);
  return res.data;
}

export async function fetchRegions() {
  const res = await axios.get(`${API_BASE}/api/regions`);
  return res.data;
}

export async function fetchMetricsBySport(sportCode) {
  const res = await axios.get(`${API_BASE}/api/metrics`, {
    params: { sport: sportCode },
  });
  return res.data;
}

export async function fetchRank(sportCode, topN = 10) {
  const res = await axios.get(`${API_BASE}/api/rank`, {
    params: { sport: sportCode, top_n: topN },
  });
  return res.data;
}
