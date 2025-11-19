from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict

from data_loader import load_data

app = FastAPI(title="SpoMap API")

# CORS (프론트엔드에서 호출 가능하게)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용: 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서버 시작 시 한 번 데이터 로딩
REGIONS, METRICS, SPORTS = load_data()
SPORT_CODE_LIST = [code for code, label in SPORTS]


class Region(BaseModel):
    id: str
    name: str
    lat: float
    lng: float


class Metric(BaseModel):
    region_id: str
    sport: str
    demand_score: float
    supply_score: float
    edi: float


class RankedRegion(BaseModel):
    region_id: str
    region_name: str
    edi: float
    demand_score: float
    supply_score: float


@app.get("/api/sports", response_model=List[Dict[str, str]])
def get_sports():
    """
    사용 가능한 스포츠 카테고리 목록 (코드 + 라벨)
    """
    return [{"code": code, "label": label} for code, label in SPORTS]


@app.get("/api/regions", response_model=List[Region])
def get_regions():
    """
    지도에 뿌릴 시군구 리스트
    """
    return [Region(**r) for r in REGIONS]


@app.get("/api/metric", response_model=Metric)
def get_metric(region_id: str, sport: str):
    """
    특정 지역 + 특정 스포츠의 수요/공급/EDI
    """
    if sport not in SPORT_CODE_LIST:
        raise HTTPException(status_code=404, detail="Unsupported sport")
    key = (region_id, sport)
    if key not in METRICS:
        raise HTTPException(status_code=404, detail="Metric not found")
    m = METRICS[key]
    return Metric(
        region_id=region_id,
        sport=sport,
        demand_score=m["demand_score"],
        supply_score=m["supply_score"],
        edi=m["edi"],
    )


@app.get("/api/metrics", response_model=List[Metric])
def get_metrics(sport: str):
    """
    특정 스포츠에 대해 모든 지역의 메트릭 목록
    """
    if sport not in SPORT_CODE_LIST:
        raise HTTPException(status_code=404, detail="Unsupported sport")
    result: List[Metric] = []
    for (rid, sp), m in METRICS.items():
        if sp == sport:
            result.append(
                Metric(
                    region_id=rid,
                    sport=sp,
                    demand_score=m["demand_score"],
                    supply_score=m["supply_score"],
                    edi=m["edi"],
                )
            )
    if not result:
        raise HTTPException(status_code=404, detail="No metrics for this sport")
    return result


@app.get("/api/rank", response_model=List[RankedRegion])
def get_rank(sport: str, top_n: int = 10):
    """
    특정 스포츠에 대해 EDI 큰 순으로 상위 지역 랭킹
    """
    if sport not in SPORT_CODE_LIST:
        raise HTTPException(status_code=404, detail="Unsupported sport")

    region_ids_with_coord = {r["id"] for r in REGIONS}
    items = []
    for (rid, sp), m in METRICS.items():
        if sp == sport and rid in region_ids_with_coord:
            items.append((rid, m))

    items.sort(key=lambda x: x[1]["edi"], reverse=True)
    top_n = min(top_n, len(items))

    id_to_name = {r["id"]: r["name"] for r in REGIONS}
    result: List[RankedRegion] = []
    for rid, m in items[:top_n]:
        result.append(
            RankedRegion(
                region_id=rid,
                region_name=id_to_name.get(rid, rid),
                edi=m["edi"],
                demand_score=m["demand_score"],
                supply_score=m["supply_score"],
            )
        )
    return result
