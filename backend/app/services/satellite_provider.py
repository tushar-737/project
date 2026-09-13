"""
NER LandslideAI - Real Sentinel-2 Satellite Provider

Fetches real Sentinel-2 L2A imagery from the
Microsoft Planetary Computer.

Performance improvements:

- In-memory satellite observation caching
- Prevents repeated Sentinel-2 API calls
- Thread-safe cache access
- Cache expiry
- Failed-request caching
- Faster /predict-all
- Faster dashboard

Satellite bands:

B04 -> Red
B08 -> Near Infrared

NDVI:

NDVI = (NIR - RED) / (NIR + RED)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
import threading

import numpy as np
import planetary_computer
import rasterio
from pystac_client import Client


# ============================================================
# CONFIGURATION
# ============================================================

STAC_URL = (
    "https://planetarycomputer.microsoft.com/api/stac/v1"
)

# Search recent Sentinel-2 observations.
SEARCH_DAYS = 120

# Never use very old satellite observations.
MAX_OBSERVATION_AGE_DAYS = 90

# Reject extremely cloudy scenes.
MAX_CLOUD_COVER = 70

# Prefer scenes with this cloud cover or lower.
PREFERRED_CLOUD_COVER = 40

# ============================================================
# CACHE CONFIGURATION
# ============================================================

# Real satellite observations do not need to be downloaded
# repeatedly during every prediction.
#
# Sentinel-2 imagery does not change every few seconds,
# so caching for several hours is safe.

CACHE_DURATION = timedelta(hours=6)

# If the provider fails, cache the failure briefly.
# This prevents repeatedly calling the remote API when it
# is unavailable.

FAILURE_CACHE_DURATION = timedelta(minutes=5)


# ============================================================
# SATELLITE OBSERVATION
# ============================================================

@dataclass

class RealSatelliteObservation:

    raw_ndvi: float

    vegetation_index: float

    source: str

    observation_date: str

    cloud_cover: float

    observation_age_days: int

    freshness_status: str

    def as_dict(self) -> dict:

        return {

            "raw_ndvi": self.raw_ndvi,

            "vegetation_index":
                self.vegetation_index,

            "source":
                self.source,

            "observation_date":
                self.observation_date,

            "cloud_cover":
                self.cloud_cover,

            "observation_age_days":
                self.observation_age_days,

            "freshness_status":
                self.freshness_status,

        }


# ============================================================
# CACHE ENTRY
# ============================================================

@dataclass

class SatelliteCacheEntry:

    observation: Optional[RealSatelliteObservation]

    created_at: datetime

    expires_at: datetime


# ============================================================
# SATELLITE CACHE
# ============================================================

_satellite_cache: dict[
    tuple[float, float],
    SatelliteCacheEntry,
] = {}


_cache_lock = threading.Lock()


# ============================================================
# CACHE KEY
# ============================================================

def get_cache_key(
    latitude: float,
    longitude: float,
) -> tuple[float, float]:

    """
    Create a stable cache key.

    Coordinates are rounded because tiny floating point
    differences should not trigger a new satellite request.
    """

    return (

        round(latitude, 4),

        round(longitude, 4),

    )


# ============================================================
# GET CACHED OBSERVATION
# ============================================================

def get_cached_observation(
    latitude: float,
    longitude: float,
) -> tuple[bool, Optional[RealSatelliteObservation]]:

    """
    Returns:

    (cache_found, observation)

    observation may be None when a failed request
    was cached temporarily.
    """

    cache_key = get_cache_key(
        latitude,
        longitude,
    )

    current_time = datetime.now(
        timezone.utc
    )

    with _cache_lock:

        entry = _satellite_cache.get(
            cache_key
        )

        if entry is None:

            return False, None

        if current_time >= entry.expires_at:

            del _satellite_cache[
                cache_key
            ]

            return False, None

        return True, entry.observation


# ============================================================
# SAVE CACHE
# ============================================================

def cache_observation(
    latitude: float,
    longitude: float,
    observation: Optional[RealSatelliteObservation],
) -> None:

    """
    Save a satellite observation.

    Successful observations are cached longer.

    Failed observations are cached briefly.
    """

    cache_key = get_cache_key(
        latitude,
        longitude,
    )

    current_time = datetime.now(
        timezone.utc
    )

    if observation is None:

        expires_at = (

            current_time
            +
            FAILURE_CACHE_DURATION

        )

    else:

        expires_at = (

            current_time
            +
            CACHE_DURATION

        )

    entry = SatelliteCacheEntry(

        observation=observation,

        created_at=current_time,

        expires_at=expires_at,

    )

    with _cache_lock:

        _satellite_cache[
            cache_key
        ] = entry


# ============================================================
# CLEAR CACHE
# ============================================================

def clear_satellite_cache() -> int:

    """
    Clear all cached satellite observations.

    Useful for:

    - Testing
    - Demo mode
    - Manual refresh
    """

    with _cache_lock:

        count = len(
            _satellite_cache
        )

        _satellite_cache.clear()

    return count


# ============================================================
# GET CACHE STATISTICS
# ============================================================

def get_satellite_cache_stats() -> dict:

    """
    Return current satellite cache information.
    """

    current_time = datetime.now(
        timezone.utc
    )

    with _cache_lock:

        expired_keys = [

            key

            for key, entry
            in _satellite_cache.items()

            if current_time
            >= entry.expires_at

        ]

        for key in expired_keys:

            del _satellite_cache[key]

        successful_entries = sum(

            1

            for entry
            in _satellite_cache.values()

            if entry.observation
            is not None

        )

        failed_entries = sum(

            1

            for entry
            in _satellite_cache.values()

            if entry.observation
            is None

        )

        return {

            "total_entries":
                len(_satellite_cache),

            "successful_entries":
                successful_entries,

            "failed_entries":
                failed_entries,

            "cache_duration_hours":
                CACHE_DURATION.total_seconds()
                / 3600,

        }


# ============================================================
# CALCULATE NDVI
# ============================================================

def calculate_ndvi(
    red_band,
    nir_band,
) -> Optional[float]:

    """
    Calculate NDVI.

    NDVI = (NIR - RED) / (NIR + RED)

    Raw NDVI normally ranges from -1 to +1.
    """

    red = red_band.astype(
        np.float32
    )

    nir = nir_band.astype(
        np.float32
    )

    denominator = nir + red

    valid_mask = (
        denominator != 0
    )

    if not np.any(valid_mask):

        return None

    ndvi = np.full(

        red.shape,

        np.nan,

        dtype=np.float32,

    )

    ndvi[valid_mask] = (

        nir[valid_mask]

        -

        red[valid_mask]

    ) / denominator[valid_mask]

    valid_values = ndvi[
        ~np.isnan(ndvi)
    ]

    if valid_values.size == 0:

        return None

    return float(
        np.median(
            valid_values
        )
    )


# ============================================================
# READ SATELLITE BAND SAMPLE
# ============================================================

def read_band_sample(
    band_url: str,
    latitude: float,
    longitude: float,
) -> Optional[np.ndarray]:

    """
    Read a small pixel window around the monitored
    latitude and longitude.

    This avoids downloading the complete
    Sentinel-2 raster.
    """

    try:

        with rasterio.open(
            band_url
        ) as dataset:

            from rasterio.warp import transform

            from rasterio.windows import Window

            xs, ys = transform(

                "EPSG:4326",

                dataset.crs,

                [longitude],

                [latitude],

            )

            x = xs[0]

            y = ys[0]

            row, col = dataset.index(
                x,
                y,
            )

            window_size = 9

            row_start = max(

                row
                -
                window_size // 2,

                0,

            )

            col_start = max(

                col
                -
                window_size // 2,

                0,

            )

            window = Window(

                col_start,

                row_start,

                window_size,

                window_size,

            )

            data = dataset.read(

                1,

                window=window,

                boundless=True,

                fill_value=0,

            )

            return data

    except Exception as error:

        print(

            "Satellite band read error:",

            str(error),

        )

        return None


# ============================================================
# DETERMINE DATA FRESHNESS
# ============================================================

def get_freshness_status(
    observation_age_days: int,
) -> str:

    if observation_age_days <= 7:

        return "FRESH"

    elif observation_age_days <= 30:

        return "RECENT"

    elif observation_age_days <= 90:

        return "AGING"

    return "OLD"


# ============================================================
# PARSE OBSERVATION DATE
# ============================================================

def get_item_datetime(
    item,
) -> Optional[datetime]:

    observation_datetime = (

        item.properties.get(
            "datetime"
        )

    )

    if observation_datetime is None:

        if item.datetime:

            return item.datetime

        return None

    try:

        parsed_datetime = (
            datetime.fromisoformat(

                str(
                    observation_datetime
                ).replace(

                    "Z",

                    "+00:00",

                )

            )
        )

        if parsed_datetime.tzinfo is None:

            parsed_datetime = (
                parsed_datetime.replace(
                    tzinfo=timezone.utc
                )
            )

        return parsed_datetime

    except Exception:

        return None


# ============================================================
# CALCULATE OBSERVATION AGE
# ============================================================

def get_observation_age_days(
    observation_datetime: datetime,
    current_datetime: datetime,
) -> int:

    age = (

        current_datetime

        -

        observation_datetime

    ).days

    return max(
        0,
        age,
    )


# ============================================================
# SELECT BEST SATELLITE SCENE
# ============================================================

def select_best_scene(
    items,
    current_datetime: datetime,
):

    candidates = []

    for item in items:

        observation_datetime = (
            get_item_datetime(item)
        )

        if observation_datetime is None:

            continue

        observation_age_days = (
            get_observation_age_days(

                observation_datetime,

                current_datetime,

            )
        )

        if (

            observation_age_days

            >

            MAX_OBSERVATION_AGE_DAYS

        ):

            continue

        cloud_cover = float(

            item.properties.get(

                "eo:cloud_cover",

                100,

            )
        )

        if cloud_cover > MAX_CLOUD_COVER:

            continue

        candidates.append(

            (

                item,

                observation_datetime,

                observation_age_days,

                cloud_cover,

            )
        )

    if not candidates:

        return None

    candidates.sort(

        key=lambda candidate: (

            candidate[2],

            candidate[3],

        )
    )

    return candidates[0]


# ============================================================
# FETCH SATELLITE OBSERVATION
# ============================================================

def fetch_real_satellite_observation(
    latitude: float,
    longitude: float,
) -> Optional[RealSatelliteObservation]:

    """
    Perform the actual remote Sentinel-2 request.

    This function should NOT normally be called directly.

    Use:

    get_real_satellite_observation()

    which includes caching.
    """

    try:

        catalog = Client.open(

            STAC_URL,

            modifier=(
                planetary_computer.sign_inplace
            ),

        )

        end_date = datetime.now(
            timezone.utc
        )

        start_date = (

            end_date

            -

            timedelta(
                days=SEARCH_DAYS
            )

        )

        date_range = (

            f"{start_date.strftime('%Y-%m-%d')}/"

            f"{end_date.strftime('%Y-%m-%d')}"

        )

        offset = 0.01

        bbox = [

            longitude - offset,

            latitude - offset,

            longitude + offset,

            latitude + offset,

        ]

        search = catalog.search(

            collections=[
                "sentinel-2-l2a"
            ],

            bbox=bbox,

            datetime=date_range,

            query={

                "eo:cloud_cover": {

                    "lt":
                        MAX_CLOUD_COVER

                }

            },

            max_items=50,

        )

        items = list(
            search.items()
        )

        if not items:

            print(

                "No Sentinel-2 observations found."

            )

            return None

        selected_scene = (
            select_best_scene(

                items=items,

                current_datetime=end_date,

            )
        )

        if selected_scene is None:

            print(

                "No recent suitable Sentinel-2 "
                "observation found."

            )

            return None

        (

            item,

            observation_datetime,

            observation_age_days,

            cloud_cover,

        ) = selected_scene

        freshness_status = (
            get_freshness_status(
                observation_age_days
            )
        )

        if (

            "B04" not in item.assets

            or

            "B08" not in item.assets

        ):

            print(

                "Required Sentinel-2 bands "
                "not available."

            )

            return None

        signed_item = (
            planetary_computer.sign(
                item
            )
        )

        red_band_url = (

            signed_item.assets[
                "B04"
            ].href

        )

        nir_band_url = (

            signed_item.assets[
                "B08"
            ].href

        )

        red_data = read_band_sample(

            band_url=red_band_url,

            latitude=latitude,

            longitude=longitude,

        )

        if red_data is None:

            return None

        nir_data = read_band_sample(

            band_url=nir_band_url,

            latitude=latitude,

            longitude=longitude,

        )

        if nir_data is None:

            return None

        raw_ndvi = calculate_ndvi(

            red_band=red_data,

            nir_band=nir_data,

        )

        if raw_ndvi is None:

            print(
                "Unable to calculate NDVI."
            )

            return None

        vegetation_index = (

            raw_ndvi + 1.0

        ) / 2.0

        vegetation_index = max(

            0.0,

            min(

                1.0,

                vegetation_index,

            ),

        )

        print(

            "Real Sentinel-2 observation:",

            observation_datetime.isoformat(),

            "| NDVI:",

            round(
                raw_ndvi,
                4,
            ),

            "| Cloud:",

            round(
                cloud_cover,
                2,
            ),

            "%",

            "| Age:",

            observation_age_days,

            "days",

            "| Freshness:",

            freshness_status,

        )

        return RealSatelliteObservation(

            raw_ndvi=round(
                raw_ndvi,
                4,
            ),

            vegetation_index=round(
                vegetation_index,
                4,
            ),

            source=(
                "SENTINEL_2_"
                "MICROSOFT_PLANETARY_COMPUTER"
            ),

            observation_date=(
                observation_datetime.isoformat()
            ),

            cloud_cover=round(
                cloud_cover,
                2,
            ),

            observation_age_days=(
                observation_age_days
            ),

            freshness_status=(
                freshness_status
            ),

        )

    except Exception as error:

        print(

            "Satellite provider error:",

            str(error),

        )

        return None


# ============================================================
# GET REAL SENTINEL-2 OBSERVATION
# ============================================================

def get_real_satellite_observation(
    latitude: float,
    longitude: float,
) -> Optional[RealSatelliteObservation]:

    """
    Get a real Sentinel-2 observation.

    Uses cache before making a remote API request.
    """

    cache_found, cached_observation = (
        get_cached_observation(

            latitude=latitude,

            longitude=longitude,

        )
    )

    if cache_found:

        print(

            "Satellite cache hit:",

            round(latitude, 4),

            round(longitude, 4),

        )

        return cached_observation

    print(

        "Satellite cache miss. "
        "Fetching Sentinel-2 data:",

        round(latitude, 4),

        round(longitude, 4),

    )

    observation = (
        fetch_real_satellite_observation(

            latitude=latitude,

            longitude=longitude,

        )
    )

    cache_observation(

        latitude=latitude,

        longitude=longitude,

        observation=observation,

    )

    return observation