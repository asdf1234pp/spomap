from pathlib import Path
import pandas as pd
import numpy as np
import re
from typing import Dict, Tuple, List

# 1. 기본 경로 설정
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# 2. 데이터 파일 경로 (네가 넣은 파일 이름 그대로)
FILE_FITNESS = DATA_DIR / "KS_NFA_FTNESS_MESURE_STTUS_202507.csv"
FILE_VOUCH = DATA_DIR / "KS_SPORTS_VOUCH_FCLTY_INFO_202507.csv"
FILE_PUBLIC = DATA_DIR / "KS_WNTY_PUBLIC_PHSTRN_FCLTY_STTUS_202507.csv"
FILE_POP = DATA_DIR / "KCB_SIGNGU_DATA3_09_202509 (1).csv"

# 3. 사용할 스포츠 카테고리 (내부 코드용)
SPORT_LIST = ["ball_sports", "fitness", "swimming", "pilates_yoga"]

# 각 카테고리에 들어가는 한글 키워드들
SPORT_CATS = {
    "fitness": ["헬스", "피트니스", "PT", "짐", "웨이트", "보디빌딩"],
    "pilates_yoga": ["필라테스", "요가"],
    "swimming": ["수영"],
    "ball_sports": ["축구", "풋살", "농구", "배드민턴", "족구", "야구", "테니스", "탁구", "핸드볼", "배구"],
}


def categorize_text(txt: str) -> List[str]:
    """
    텍스트(ITEM_NM, FCLTY_NM 등)를 보고 어떤 스포츠 카테고리에 속하는지 분류
    """
    if not isinstance(txt, str):
        return []
    cats = set()
    for cat, kws in SPORT_CATS.items():
        for kw in kws:
            if kw in txt:
                cats.add(cat)
    return list(cats)


def categorize_public_row(row) -> List[str]:
    """
    공공체육시설 한 행을 보고 카테고리 추론
    FCLTY_TY_NM / INDUTY_NM / FCLTY_NM 등을 합쳐서 본다.
    """
    texts = []
    for col in ["FCLTY_TY_NM", "INDUTY_NM", "FCLTY_NM"]:
        val = row.get(col, "")
        texts.append(str(val) if isinstance(val, str) else "")
    joined = " ".join(texts)
    cats = set()
    for cat, kws in SPORT_CATS.items():
        for kw in kws:
            if kw in joined:
                cats.add(cat)
    # 추가 휴리스틱
    if "간이운동장" in joined or "운동장" in joined or "구장" in joined:
        cats.add("ball_sports")
    if "체육관" in joined or "체육센터" in joined or "헬스장" in joined:
        cats.add("fitness")
    if "수영장" in joined:
        cats.add("swimming")
    if "요가" in joined or "필라테스" in joined:
        cats.add("pilates_yoga")
    return list(cats)


def explode_categories(df: pd.DataFrame, region_col: str) -> pd.DataFrame:
    """
    categories: [fitness, pilates_yoga, ...] 리스트를 sport_cat 행으로 폭발(explode)
    """
    df2 = df[[region_col, "categories"]].copy()
    df2 = df2[df2["categories"].map(lambda x: bool(x))]
    df2 = df2.explode("categories")
    df2 = df2.rename(columns={"categories": "sport_cat", region_col: "region_id"})
    return df2


def normalize_series(s: pd.Series) -> pd.Series:
    """
    0~1 사이로 정규화. 값이 전부 같으면 0.5로 통일.
    (지금은 직접 사용하진 않지만, 필요시 대비로 놔둠)
    """
    s = s.astype(float)
    min_v = s.min()
    max_v = s.max()
    if np.isnan(min_v) or np.isnan(max_v) or max_v - min_v < 1e-9:
        return pd.Series(0.5, index=s.index)
    return (s - min_v) / (max_v - min_v)


def guess_region_id_from_cnter(cnter_nm: str, pop_df: pd.DataFrame) -> str | None:
    """
    국민체력100 측정센터 이름(CNTER_NM)을 인구데이터의 시군구 코드에 매핑.
    완벽하진 않지만 '동구(인천)', '목포', '고양' 같은 문자열 기반으로 추정.
    """
    if not isinstance(cnter_nm, str) or not cnter_nm.strip():
        return None
    name = cnter_nm.strip()
    city_hint = None
    m = re.match(r"(.+)\((.+)\)", name)
    if m:
        base = m.group(1).strip()
        city_hint = m.group(2).strip()
    else:
        base = name

    candidates = pop_df
    if city_hint:
        candidates = candidates[candidates["SIGNGU_NM"].str.contains(city_hint, na=False)]

    # 1) short_name 안에 base 포함
    cand = candidates[candidates["short_name"].str.contains(base, na=False)]
    if len(cand) == 1:
        return cand.iloc[0]["region_id"]
    if len(cand) > 1:
        return cand.iloc[0]["region_id"]

    # 2) base + 시/군/구
    for suffix in ["시", "군", "구"]:
        target = base + suffix
        cand = candidates[candidates["short_name"] == target]
        if len(cand) == 1:
            return cand.iloc[0]["region_id"]
        if len(cand) > 1:
            return cand.iloc[0]["region_id"]

    # 3) 시군구 전체 이름에 base 포함
    cand = candidates[candidates["SIGNGU_NM"].str.contains(base, na=False)]
    if len(cand) >= 1:
        return cand.iloc[0]["region_id"]

    return None


def load_data():
    """
    4개 CSV를 모두 읽어서
      - REGIONS: 지도에 뿌릴 시군구 리스트
      - METRICS: (region_id, sport)별 demand/supply/edi
      - SPORTS: 사용 가능한 스포츠 카테고리 목록
    을 만들어서 반환.
    """
    # 1) 인구 데이터 (시군구별 연령대 인구)
    pop = pd.read_csv(FILE_POP)
    pop["region_id"] = pop["SIGNGU_CD"].astype(str).str.zfill(5)
    age_cols = [c for c in pop.columns if "POP" in c]
    pop["total_pop"] = pop[age_cols].sum(axis=1)
    pop["active_pop"] = pop[["N20S_POPLTN_CO", "N30S_POPLTN_CO", "N40S_POPLTN_CO"]].sum(axis=1)
    pop["short_name"] = pop["SIGNGU_NM"].str.split().str[-1]

    # 2) 스포츠강좌이용권 시설 (좌표 + 종목 정보)
    vouch = pd.read_csv(FILE_VOUCH)
    vouch["region_id"] = vouch["SIGNGU_CD"].astype(str).str.zfill(5)
    vouch["categories"] = vouch["ITEM_NM"].apply(categorize_text)

    # 3) 공공체육시설 정보 (공공시설 + 좌표)
    pub = pd.read_csv(FILE_PUBLIC)
    pub["region_id"] = pub["POSESN_MBY_SIGNGU_CD"].apply(
        lambda x: f"{int(x/100000):05d}" if pd.notna(x) else None
    )
    pub["categories"] = pub.apply(categorize_public_row, axis=1)

    # 4) 국민체력100 측정 데이터 (센터 이름 → 시군구 코드 추정)
    fit = pd.read_csv(FILE_FITNESS)
    fit["region_id"] = fit["CNTER_NM"].apply(lambda nm: guess_region_id_from_cnter(nm, pop))
    fit_region_counts = (
        fit.dropna(subset=["region_id"])
        .groupby("region_id")
        .size()
        .rename("fitness_cnt")
        .reset_index()
    )

    # 5) 지역 좌표 (바우처 + 공공시설 좌표 평균)
    coords = []
    if "FCLTY_Y_CRDNT_VALUE" in vouch.columns:
        tmp = vouch[["region_id", "FCLTY_Y_CRDNT_VALUE", "FCLTY_X_CRDNT_VALUE"]].rename(
            columns={"FCLTY_Y_CRDNT_VALUE": "lat", "FCLTY_X_CRDNT_VALUE": "lng"}
        )
        coords.append(tmp)
    if "FCLTY_LA" in pub.columns:
        tmp = pub[["region_id", "FCLTY_LA", "FCLTY_LO"]].rename(
            columns={"FCLTY_LA": "lat", "FCLTY_LO": "lng"}
        )
        coords.append(tmp)
    coords_df = pd.concat(coords, ignore_index=True)
    coords_df = coords_df.dropna(subset=["region_id", "lat", "lng"])
    region_coords = coords_df.groupby("region_id").agg({"lat": "mean", "lng": "mean"}).reset_index()

    # 6) 공급 지표 계산 (sport별 지역당 시설 수 → 인구 10만 명당 수 → 백분위 점수)
    vouch_cat = explode_categories(vouch, "region_id")
    pub_cat = explode_categories(pub, "region_id")

    vouch_supply = vouch_cat.groupby(["region_id", "sport_cat"]).size().rename("vouch_cnt")
    pub_supply = pub_cat.groupby(["region_id", "sport_cat"]).size().rename("pub_cnt")

    supply = vouch_supply.to_frame().join(pub_supply, how="outer").fillna(0)
    supply["supply_raw"] = supply["vouch_cnt"] + supply["pub_cnt"]
    supply = supply.reset_index()
    supply = supply.merge(pop[["region_id", "total_pop"]], on="region_id", how="left")
    supply = supply.dropna(subset=["total_pop"])
    supply["supply_per_100k"] = supply["supply_raw"] / (supply["total_pop"] / 100000.0)

    # ▶ 변경 포인트 1: min-max 대신 "백분위 랭크" 기반 점수로 변환
    supply_scores: Dict[Tuple[str, str], float] = {}
    for sport in SPORT_LIST:
        sub = supply[supply["sport_cat"] == sport].copy()
        if sub.empty:
            continue
        # supply_per_100k가 낮은 지역은 낮은 백분위, 높은 지역은 높은 백분위
        # pct=True → 0~1 사이 값 (1/N, 2/N, ..., 1)
        sub["score_pct"] = sub["supply_per_100k"].rank(pct=True)
        sub["score"] = 100.0 * sub["score_pct"]
        for _, row in sub.iterrows():
            supply_scores[(row["region_id"], sport)] = float(row["score"])

    # 7) 수요 지표 계산 (active_pop + 국민체력100 측정 빈도 → 백분위 점수)
    pop2 = pop.merge(fit_region_counts, on="region_id", how="left")
    pop2["fitness_cnt"] = pop2["fitness_cnt"].fillna(0)
    pop2["active_rate"] = pop2["active_pop"] / pop2["total_pop"].replace(0, np.nan)
    pop2["fitness_per_10k"] = pop2["fitness_cnt"] / (pop2["total_pop"] / 10000.0).replace(0, np.nan)

    # ▶ 변경 포인트 2: active_rate, fitness_per_10k도 백분위 랭크로 압축
    # active_rate 백분위
    pop2["active_pct"] = pop2["active_rate"].rank(pct=True)
    # fitness_per_10k 백분위 (전부 0이거나 NaN이면 0.5로 고정)
    mask_fit = pop2["fitness_per_10k"].notna() & (pop2["fitness_per_10k"] > 0)
    if mask_fit.any():
        pop2.loc[mask_fit, "fitness_pct"] = pop2.loc[mask_fit, "fitness_per_10k"].rank(pct=True)
        pop2["fitness_pct"] = pop2["fitness_pct"].fillna(0.5)
    else:
        pop2["fitness_pct"] = 0.5

    # 0~100 점수로 변환 (여기서도 분산이 너무 크지 않게 가중 평균)
    pop2["demand_score"] = 100.0 * (
        0.7 * pop2["active_pct"] + 0.3 * pop2["fitness_pct"]
    )

    # 8) METRICS 딕셔너리 생성 (EDI = demand - supply)
    METRICS: Dict[Tuple[str, str], Dict[str, float]] = {}
    for sport in SPORT_LIST:
        for _, row in pop2.iterrows():
            rid = row["region_id"]
            demand = float(row["demand_score"])
            supply_score = float(supply_scores.get((rid, sport), 0.0))
            METRICS[(rid, sport)] = {
                "demand_score": demand,
                "supply_score": supply_score,
                "edi": demand - supply_score,
            }

    # 9) REGIONS 목록 (좌표 없는 지역은 지도에서 제외)
    regions = pop2[["region_id", "SIGNGU_NM"]].merge(region_coords, on="region_id", how="left")
    regions = regions.dropna(subset=["lat", "lng"])
    REGIONS = [
        {
            "id": str(row["region_id"]),
            "name": str(row["SIGNGU_NM"]),
            "lat": float(row["lat"]),
            "lng": float(row["lng"]),
        }
        for _, row in regions.iterrows()
    ]

    SPORTS = [
        ("ball_sports", "구기/필드종목"),
        ("fitness", "헬스/체력단련"),
        ("swimming", "수영"),
        ("pilates_yoga", "필라테스/요가"),
    ]

    return REGIONS, METRICS, SPORTS
