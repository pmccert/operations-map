# PMC CERT Incident Map — Functional Requirements Specification

## 1. Overview & Objectives

The **PMC CERT Incident Map** is a client-side, single-page web application designed for the Pine Mountain Club Community Emergency Response Team (PMC CERT). It visualizes live emergency incidents on an interactive map using data sourced dynamically from a publicly accessible Google Sheet.

The application operates without a dedicated backend server, resolving incident street addresses into geographic coordinates using a pre-generated local or remote address lookup table with built-in fuzzy matching.

---

## 2. Core Functional Requirements

### 2.1 Google Sheets Ingestion & Polling

* **FR-1.0: Startup Disaster Mode Picker**
  * On startup, the application shall present a disaster picker in the configuration modal before sheet data is loaded.
  * Users shall be able to choose **Blank Map**, **Earthquake**, **Evacuation**, or **Snow Emergency**.
  * Each picker option shall display a relevant Font Awesome icon.
  * Choosing a disaster mode shall preload the configuration specified for that mode from the disaster preset JSON file.
  * **Blank Map** shall allow loading the map with zero configured Google Sheets so the user can fully customise map layers manually.

* **FR-1.1: Sheet URL Ingestion & Multi-Sheet Configuration**
  * The application shall accept one or more Google Sheets sharing URLs (e.g., `https://docs.google.com/spreadsheets/d/{SHEET_ID}/...`).
  * Users shall be able to dynamically add and remove sheets, assign custom sheet names, and configure distinct icons, colors, and column mappings per sheet.
  * For each sheet, it shall extract the Sheet ID and Sheet Tab ID (`gid`, defaulting to `0` if not present) and convert the input URL into a direct CSV export endpoint (`https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}`).

* **FR-1.2: Periodic Polling & Real-Time Sync**
  * The application shall poll all configured Google Sheet CSV endpoints at a fixed interval of **30 seconds**.
  * Requests shall include `cache: 'no-store'` to bypass browser caching and fetch the latest live updates.
  * Markers on the map shall be added, updated in-place (location, icon, color, popup content), or removed to reflect the current sheet state on every poll.

* **FR-1.3: Robust CSV Parsing**
  * The application shall implement RFC 4180-compliant CSV parsing, properly handling multi-line inputs, commas within quoted strings, escaped quotes (`""`), and whitespace trimming.

* **FR-1.4: Automatic Column Detection**
  * Upon entering a Google Sheet URL, the application shall probe and parse the header row (first line) to detect column indices automatically using keyword heuristics for each sheet:
    * **Address Column (Required):** Matched if header contains `address`, `addr`, `location`, `street`, or `residence`.
    * **Status Column (Optional):** Matched if header contains `status`, `state`, `open`, `closed`, `condition`, or `stage`.
    * **Label Column (Optional):** Matched if header contains `label`, `desc`, `title`, `detail`, `note`, `type`, `incident`, `summary`, `comment`, or `call`.
  * Fallbacks if keywords do not match: Column A (`0`) for Address, Column B (`1`) for Status (if present), Column C (`2`) for Label (if present).

* **FR-1.5: Configurable Column Mapping per Sheet**
  * Users shall be able to manually select and override the Address, Status, and Label columns individually for each configured sheet in the startup/configuration dialog and at runtime via the **Manage Sheets** dialog.
  * **Address Column:** Required; must reference a valid column.
  * **Status Column:** Optional; can be mapped to a specific column or set to `(None — Always Open)`.
  * **Label Column:** Optional; can be mapped to a specific column or set to `(None — Default #)`.

---

### 2.2 Address Geocoding & Fuzzy Matching Engine

* **FR-2.1: Address Parsing & Sanitization**
  * Incident address strings shall be parsed into a numeric house number (with optional letter suffix, e.g., `1234` or `1234A`) and a street name.
  * US ZIP codes (5-digit `93222` and ZIP+4 `93222-1234`) and trailing commas shall be stripped before lookup.
  * Addresses without a valid leading house number shall be treated as unplottable.
  * Open Location Codes (Plus Codes), including full codes and shortened codes
    relative to Pine Mountain Club, shall be decoded directly to coordinates.

* **FR-2.2: Street Normalization**
  * Street names shall be normalized by converting to lowercase, stripping punctuation, collapsing whitespace, and expanding common road and directional abbreviations (e.g., `dr` → `drive`, `ave` → `avenue`, `st` → `street`, `rd` → `road`, `hwy` → `highway`, `n`/`s`/`e`/`w` → `north`/`south`/`east`/`west`).

* **FR-2.3: Geocoder Index & Exact Matching**
  * The application shall build a nested in-memory index from `addresses.json` (`Map<NormalizedStreet, Map<HouseNumber, Coordinates>>`).
  * An exact match occurs when the normalized street and exact house number exist in the index.

* **FR-2.4: Fuzzy Street Matching**
  * If an exact street match is not found, the geocoder shall compute the Levenshtein distance between the input street and all known street names in the index.
  * Fuzzy matching shall only trigger for normalized street strings with a length of at least 5 characters.
  * The maximum allowable edit distance threshold is `max(1, floor(street_length / 5))`.
  * If a closest street within the threshold contains the requested house number, the address is resolved as a fuzzy match and flagged with its edit distance.

* **FR-2.5: Geocoder Source Detection & Override**
  * The application shall automatically detect if an `addresses.json` file is present in the local root.
  * When local `addresses.json` is detected, the UI shall default to using it and display an **Override** button allowing the user to provide an external geocoder URL.
  * If overridden, a **Use local file** button shall allow reverting back to the local source.

* **FR-2.6: Google Geocoding API Fallback**
  * When an address cannot be resolved via exact or fuzzy matching against `addresses.json`, the application shall attempt resolution via the Google Maps Geocoding API if configured (`GOOGLE_GEOCODING_API_KEY`).
  * The application shall dynamically load the Google Maps JavaScript API client when a valid API key is present.
  * Lookups shall be disambiguated with Pine Mountain Club, CA geographic context and cached in `localStorage` (`pmc_google_geocode_cache`) to prevent redundant requests across 30-second polling cycles.
  * Addresses resolved via Google Geocoding shall be flagged with `matchType: 'google'` and displayed in the popup with a `(Google Geocoded)` badge.

* **FR-2.7: Unmatched Address Handling**
  * If an address cannot be resolved via exact matching, fuzzy matching, or Google Geocoding fallback, the marker shall not be plotted on the map.
  * Unmatched addresses shall be logged to the browser console and counted in the status bar summary.

---

### 2.3 Map Interface & Layer Management

* **FR-3.1: Geographic Center & Default View**
  * The map shall initialize centered on **Pine Mountain Club, CA** (`34.857`, `-119.155`) at zoom level `13`.

* **FR-3.2: Basemap Switcher**
  * The map shall provide an interactive basemap layer control positioned at the top-right containing selectable basemaps:
    1. **OpenStreetMap** (Default basemap, max zoom 19)
    2. **OpenTopoMap** (Hillshaded terrain, max zoom 17)
    3. **USGS Topo** (USGS National Map topographic tiles, max zoom 20)
    4. **USGS Imagery** (USGS National Map aerial imagery tiles, max zoom 20)
    5. **USGS Imagery Topo** (USGS National Map aerial imagery with topographic and road overlay, max zoom 20)
    6. **Esri World Imagery** (Esri high-resolution satellite imagery tiles, max zoom 19)
    7. **Esri Clarity** (Esri cloud-free archival high-resolution satellite imagery tiles, max zoom 19)

* **FR-3.3: Basemap Zoom Availability Alert**
  * If a tile set is selected that does not support the requested zoom level (e.g., current zoom exceeds the active tile layer's `maxZoom` or is below `minZoom`), the application shall display a small error alert in the lower-right hand corner indicating that the requested zoom level is not available for this base map.
  * The alert shall automatically dismiss when the map zoom level returns to a supported range or when switching to a basemap that supports the current zoom level.

* **FR-3.4: Third-Party Map Layers**
  * The map shall provide selectable overlay layers for known fire incidents
    (National Interagency Fire Center data), nearby ADS-B aircraft, and the
    California Geological Survey landslide risk map.
  * The California Geological Survey landslide risk map shall support map zoom
    up to level 20 while over-zooming its native tiles from level 16.
  * ArcGIS-backed spatial tile overlays shall preserve visibility when users zoom
    beyond a layer's native tile resolution by displaying the highest available
    native tiles at higher map zoom levels.
  * Third-party overlays shall load on demand when selected from the layer menu,
    appear as entries in the legend while enabled, and be hideable from that
    legend without changing configured Google Sheet incidents.

---

### 2.4 Incident Marker Rendering & Status

* **FR-4.1: Distinct Marker per Row across Multiple Sheets**
  * Every row in any configured Google Sheet with a non-empty address shall represent a distinct emergency incident.
  * Markers shall be uniquely tracked per sheet to avoid collisions across multiple sheets.

* **FR-4.2: Open vs. Closed Status Evaluation**
  * Incident status shall be determined from the mapped Status column (case-insensitive) of each sheet.
  * A value of `closed` designates a **Closed** incident.
  * Any other value (or if the Status column is unmapped/none) designates an **Open** incident.

* **FR-4.3: Visual Distinction by Status & Sheet Styling**
  * **Open Incidents:** Rendered with a solid circular badge using the sheet's configured color, full opacity, the sheet's chosen white vector icon, and prominent drop shadow.
  * **Closed Incidents:** Rendered with a grey circular badge (`#7f8c8d`), reduced opacity (`0.55`), the sheet's chosen white vector icon, and reduced drop shadow.

---

### 2.5 Popup Details & Interaction

* **FR-5.1: Incident Popup Content**
  * Clicking any incident marker shall open a Leaflet popup displaying:
    * **Sheet Indicator:** Sheet name accompanied by a colored indicator matching the sheet's color.
    * **Title/Label:** The value from the Label column, or fallback default `Incident #{Row Number}`.
    * **Status Badge:** A colored badge pill (`Open` in the sheet's configured color or `Closed` in grey).
    * **Resolved Address:**
      * Exact matches: Display canonical address.
      * Fuzzy matches: Display canonical address with a `(fuzzy)` indicator and an edit distance tooltip.
      * Google Geocoded matches: Display resolved address with a `(Google Geocoded)` indicator.
      * Unmatched / error states: Display warning note and raw input address.
    * **Coordinates:** Latitude and longitude formatted to 5 decimal places (e.g., `Lat: 34.85700, Lon: -119.15500`).

---

### 2.6 Map Legend & Closed Incident Filtering

* **FR-6.1: Interactive Multi-Sheet Map Legend**
  * A persistent legend control shall be positioned in the top-right corner of the map.
  * The legend shall display an entry for every configured sheet showing its custom icon, badge color, and sheet name.
  * The legend shall include color-class entries for enabled third-party overlays
    that render multiple risk/susceptibility classes (such as the landslide risk layer).
  * The legend shall automatically update whenever sheets are added, modified, or removed.

* **FR-6.2: Show / Hide Closed Incidents Toggle**
  * The legend shall include an interactive checkbox labeled **Closed** (checked by default).
  * Unchecking the box shall immediately remove all closed incident markers across all sheets from the map.
  * Re-checking the box shall restore all closed incident markers without triggering a network fetch.

---

### 2.7 Icon and Color Customization System

* **FR-7.1: Selectable Font Awesome Incident Icons & Colors**
  * The application shall support selecting an active incident icon from 10 Font Awesome 6 vector quick presets for each sheet:
    1. **Emergency** (`fa-solid fa-bell-concierge`) — *Default*
    2. **Fire** (`fa-solid fa-fire`)
    3. **Medical** (`fa-solid fa-kit-medical`)
    4. **Vehicle** (`fa-solid fa-car-burst`)
    5. **Hazard** (`fa-solid fa-triangle-exclamation`)
    6. **Search** (`fa-solid fa-magnifying-glass`)
    7. **Wildlife** (`fa-solid fa-paw`)
    8. **Rescue** (`fa-solid fa-person-falling`)
    9. **Pin** (`fa-solid fa-location-dot`)
    10. **Star** (`fa-solid fa-star`)
  * The application shall provide an interactive Font Awesome icon picker dialog allowing users to browse, search (by keyword/name), filter by category (Emergency, Medical, Transport, Warning, Maps, Nature, All), switch styles (Solid, Regular, Brands), or input any custom Font Awesome icon class with live preview.
  * The application shall provide an integrated color picker, direct hex code input, and preset color palette allowing each sheet to have any custom badge color.

* **FR-7.2: Icon & Color Updates Across Components**
  * Selecting an icon or color for any sheet shall immediately update:
    * All active markers corresponding to that sheet currently rendered on the map.
    * The sheet's preview in the map legend and dialog badge previews.

* **FR-7.3: Dropdown Category Styling**
  * Users shall be able to select an optional Category column for each sheet.
  * When a Category column is selected, the application shall use the Google Sheets API
    (when authenticated) to read its data-validation dropdown options, including options
    sourced from another cell range.
  * Each discovered category option shall support its own FontAwesome icon and background
    color. Category styling shall override the sheet default for open incident markers,
    while preserving the existing grey rendering for closed incidents.

---

### 2.8 Runtime Toolbar & Modal Controls

* **FR-8.1: Top-Left Toolbar**
  * A fixed floating **Map Actions** menu shall provide:
    * **Manage Sheets:** Opens the full sheet configuration modal to add, rename, edit URLs, customize icons/colors, adjust column mappings, or delete sheets; includes a **Cancel** action to discard uncommitted changes and return to the active map.
    * The same modal shall continue to expose the disaster picker so users can switch between startup presets later.

* **FR-8.2: Status Bar Feedback**
  * A bottom-center floating pill shall report operational status and diagnostics:
    * Connection states: `Waiting for sheet configuration…`, `Detecting columns…`, `Loading geocoder…`, `Fetching data…`.
    * Polling results: Timestamp of last successful fetch, total incident count, total sheets, open incident count, closed incident count, and count of unmatched addresses.
    * Error messages: Informative network and parsing error messages.

* **FR-8.3: Commit Metadata Display**
  * A discreet floating badge in the lower-left corner shall display the deployed commit ID (with a direct link to the commit on GitHub) and the commit timestamp/date for version tracking.

### 2.9 Custom Map Features

* **FR-8.4: User-Drawn Geometries**
  * The application shall allow users to draw points, lines, and polygons directly on the map.
  * Each feature shall have a custom color, FontAwesome icon, and label, plus an optional description stored locally in the browser.
  * The description shall not be displayed in the map popup or otherwise rendered on the map.
* **FR-8.5: Local Persistence & Management**
  * Custom features shall be persisted in browser local storage and restored when the map is reopened.
  * Users shall be able to delete saved custom features from the Custom Features dialog.

---

## 3. Address Extraction CLI Tool (`scripts/fetch_addresses.py`)

* **FR-9.1: Geographic Boundary Input**
  * The standalone CLI tool shall query OpenStreetMap via Overpass API to generate geocoder lookup tables.
  * Shall accept boundaries via mutually exclusive parameters:
    * `--bbox south,west,north,east`: Decimal degree bounding box coordinates with validation (`south < north`, `west < east`).
    * `--poly FILE`: Path to a polygon boundary file (GeoJSON Feature/Polygon, JSON coordinate array, or WKT `POLYGON(...)`).

* **FR-9.2: Overpass API Querying & Resilience**
  * Shall query `https://overpass-api.de/api/interpreter` for all nodes, ways, and relations containing `addr:housenumber` and `addr:street` tags using `out center;`.
  * Shall include a customized `User-Agent` identifying the tool and repository.
  * Shall implement automatic exponential backoff retry logic for HTTP 429 rate-limiting (up to 3 retries, 5s backoff).

* **FR-9.3: Address Formatting & Deduplication**
  * Shall extract `{addr:housenumber} {addr:street}` pairs and resolve coordinates (`lat`/`lon` for nodes, `center.lat`/`center.lon` for ways/relations).
  * Shall deduplicate identical addresses (retaining the first occurrence).
  * Shall output a JSON file mapping addresses to `{ "lat": <float>, "lon": <float> }`.

---

## 4. Data Specifications & Schemas

### 4.1 Google Sheet Format (CSV Representation)

| Header Example | Description | Type / Constraints |
| :--- | :--- | :--- |
| `Address` *(Required)* | Street address with house number (e.g., `1234 Nesthorn Drive`) | String; non-empty row required |
| `Status` *(Optional)* | Incident resolution status (`open` or `closed`) | String (case-insensitive); defaults to open |
| `Label` *(Optional)* | Free-text description or incident title | String; defaults to `Incident #N` |

### 4.2 Geocoder JSON (`addresses.json`) Schema

```json
{
  "1234 Nesthorn Drive": {
    "lat": 34.85712,
    "lon": -119.15534
  },
  "56 Mil Potrero Highway": {
    "lat": 34.85123,
    "lon": -119.16245
  }
}
```

### 4.3 Disaster Preset JSON (`assets/disaster-modes.json`) Schema

```json
{
  "version": 1,
  "defaultModeId": "blank-map",
  "modes": [
    {
      "id": "earthquake",
      "label": "Earthquake",
      "description": "Preload a sheet template for quake response incidents.",
      "icon": {
        "fa": "fa-solid fa-house-crack",
        "label": "Earthquake"
      },
      "preset": {
        "geocoder": {
          "url": "",
          "useLocalFile": true
        },
        "baseLayer": "OpenStreetMap",
        "enabledThirdPartyLayers": ["Known Fire Incidents"],
        "mapView": {
          "lat": 34.857,
          "lng": -119.155,
          "zoom": 13
        },
        "sheets": [
          {
            "name": "Earthquake Incidents",
            "rawUrl": "",
            "columnMapping": {
              "address": 0,
              "status": 1,
              "label": 2,
              "category": null
            },
            "headers": ["Address", "Status", "Label"],
            "icon": {
              "fa": "fa-solid fa-house-crack",
              "label": "Earthquake"
            },
            "color": "#D97706",
            "categoryOptions": []
          }
        ]
      }
    }
  ]
}
```

* `defaultModeId` shall identify one of the entries in `modes`.
* `modes[].icon.fa` shall be a Font Awesome class string used in the modal picker.
* `preset.sheets` may be empty to support a blank-map startup.
* `preset.geocoder`, `preset.baseLayer`, `preset.enabledThirdPartyLayers`, and `preset.mapView` are optional; omitted values fall back to normal application defaults.
* `preset.sheets[].rawUrl` is optional so a preset can define sheet styling before a Google Sheet URL is attached.
* `assets/disaster-modes.json` shall be the single source of truth for disaster presets; the application shall not duplicate preset definitions in code.

---

## 5. Build, Quality & CI/CD Pipeline

* **FR-10.1: Code Quality & Linting**
  * JavaScript within `index.html` shall be validated using ESLint with HTML plugin rules (`npm run lint`).
  * Python scripts shall be tested using `unittest` (`python -m unittest discover tests`).

* **FR-10.2: Continuous Deployment**
  * GitHub Actions (`deploy-pages.yml`) shall run ESLint and Python tests on every push and pull request.
  * On commits merged into `main`, the workflow shall automatically execute `fetch_addresses.py` with the Pine Mountain Club bounding box (`34.8,-119.2,34.9,-119.1`) to build `addresses.json` and publish the site to GitHub Pages.
