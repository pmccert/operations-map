# PMC CERT Incident Map — Functional Requirements Specification

## 1. Overview & Objectives

The **PMC CERT Incident Map** is a client-side, single-page web application designed for the Pine Mountain Club Community Emergency Response Team (PMC CERT). It visualizes live emergency incidents on an interactive map using data sourced dynamically from a publicly accessible Google Sheet.

The application operates without a dedicated backend server, resolving incident street addresses into geographic coordinates using a pre-generated local or remote address lookup table with built-in fuzzy matching.

---

## 2. Core Functional Requirements

### 2.1 Google Sheets Ingestion & Polling

* **FR-1.1: Sheet URL Ingestion & Parsing**
  * The application shall accept a standard Google Sheets sharing URL (e.g., `https://docs.google.com/spreadsheets/d/{SHEET_ID}/...`).
  * It shall extract the Sheet ID and Sheet Tab ID (`gid`, defaulting to `0` if not present) and convert the input URL into a direct CSV export endpoint (`https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}`).

* **FR-1.2: Periodic Polling & Real-Time Sync**
  * The application shall poll the Google Sheet CSV endpoint at a fixed interval of **30 seconds**.
  * Requests shall include `cache: 'no-store'` to bypass browser caching and fetch the latest live updates.
  * Markers on the map shall be added, updated in-place (location, icon, popup content), or removed to reflect the current sheet state on every poll.

* **FR-1.3: Robust CSV Parsing**
  * The application shall implement RFC 4180-compliant CSV parsing, properly handling multi-line inputs, commas within quoted strings, escaped quotes (`""`), and whitespace trimming.

* **FR-1.4: Automatic Column Detection**
  * Upon entering a Google Sheet URL, the application shall probe and parse the header row (first line) to detect column indices automatically using keyword heuristics:
    * **Address Column (Required):** Matched if header contains `address`, `addr`, `location`, `street`, or `residence`.
    * **Status Column (Optional):** Matched if header contains `status`, `state`, `open`, `closed`, `condition`, or `stage`.
    * **Label Column (Optional):** Matched if header contains `label`, `desc`, `title`, `detail`, `note`, `type`, `incident`, `summary`, `comment`, or `call`.
  * Fallbacks if keywords do not match: Column A (`0`) for Address, Column B (`1`) for Status (if present), Column C (`2`) for Label (if present).

* **FR-1.5: Configurable Column Mapping**
  * Users shall be able to manually select and override the Address, Status, and Label columns in the initial startup dialog and at runtime via the **Change Columns** toolbar button.
  * **Address Column:** Required; must reference a valid column.
  * **Status Column:** Optional; can be mapped to a specific column or set to `(None — Always Open)`.
  * **Label Column:** Optional; can be mapped to a specific column or set to `(None — Default #)`.

---

### 2.2 Address Geocoding & Fuzzy Matching Engine

* **FR-2.1: Address Parsing & Sanitization**
  * Incident address strings shall be parsed into a numeric house number (with optional letter suffix, e.g., `1234` or `1234A`) and a street name.
  * US ZIP codes (5-digit `93222` and ZIP+4 `93222-1234`) and trailing commas shall be stripped before lookup.
  * Addresses without a valid leading house number shall be treated as unplottable.

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

* **FR-2.6: Unmatched Address Handling**
  * If an address cannot be resolved via exact or fuzzy matching, the marker shall not be plotted on the map.
  * Unmatched addresses shall be logged to the browser console and counted in the status bar summary.

---

### 2.3 Map Interface & Layer Management

* **FR-3.1: Geographic Center & Default View**
  * The map shall initialize centered on **Pine Mountain Club, CA** (`34.857`, `-119.155`) at zoom level `13`.

* **FR-3.2: Basemap Switcher**
  * The map shall provide an interactive basemap layer control positioned at the top-right containing four selectable basemaps:
    1. **OpenStreetMap** (Default basemap, max zoom 19)
    2. **OpenTopoMap** (Hillshaded terrain, max zoom 17)
    3. **USGS Topo** (USGS National Map topographic tiles, max zoom 20)
    4. **USGS Imagery** (USGS National Map aerial imagery tiles, max zoom 20)

---

### 2.4 Incident Marker Rendering & Status

* **FR-4.1: Distinct Marker per Row**
  * Every row in the Google Sheet with a non-empty address shall represent a distinct emergency incident.

* **FR-4.2: Open vs. Closed Status Evaluation**
  * Incident status shall be determined from the mapped Status column (case-insensitive).
  * A value of `closed` designates a **Closed** incident.
  * Any other value (or if the Status column is unmapped/none) designates an **Open** incident.

* **FR-4.3: Visual Distinction by Status**
  * **Open Incidents:** Rendered with a solid red circular badge (`#e74c3c`), full opacity, white vector icon, and prominent drop shadow.
  * **Closed Incidents:** Rendered with a grey circular badge (`#7f8c8d`), reduced opacity (`0.55`), white vector icon, and reduced drop shadow.

---

### 2.5 Popup Details & Interaction

* **FR-5.1: Incident Popup Content**
  * Clicking any incident marker shall open a Leaflet popup displaying:
    * **Title/Label:** The value from the Label column, or fallback default `Incident #{Row Number}`.
    * **Status Badge:** A colored badge pill (`Open` in red or `Closed` in grey).
    * **Resolved Address:**
      * Exact matches: Display canonical address.
      * Fuzzy matches: Display canonical address with a `(fuzzy)` indicator and an edit distance tooltip.
      * Unmatched / error states: Display warning note and raw input address.
    * **Coordinates:** Latitude and longitude formatted to 5 decimal places (e.g., `Lat: 34.85700, Lon: -119.15500`).

---

### 2.6 Map Legend & Closed Incident Filtering

* **FR-6.1: Interactive Map Legend**
  * A persistent legend control shall be positioned in the top-right corner of the map.
  * The legend shall display sample icons for Open and Closed incidents.

* **FR-6.2: Show / Hide Closed Incidents Toggle**
  * The legend shall include an interactive checkbox labeled **Closed** (checked by default).
  * Unchecking the box shall immediately remove all closed incident markers from the map.
  * Re-checking the box shall restore all closed incident markers without triggering a network fetch.

---

### 2.7 Icon Customization System

* **FR-7.1: Selectable Font Awesome Incident Icons**
  * The application shall support selecting an active incident icon from 10 Font Awesome 6 vector icons:
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

* **FR-7.2: Icon Updates Across Components**
  * Selecting an icon in the startup dialog or the **Change Icon** modal shall immediately update:
    * All active markers currently rendered on the map.
    * The Open and Closed icon previews in the map legend.

---

### 2.8 Runtime Toolbar & Modal Controls

* **FR-8.1: Top-Left Toolbar**
  * A fixed floating toolbar shall provide three direct actions:
    * **Change Sheet:** Stops active polling, clears all map markers, resets geocoding cache, and opens the main configuration modal.
    * **Change Columns:** Opens a dedicated modal to adjust column assignments; applying changes immediately re-parses and re-plots data.
    * **Change Icon:** Opens a dedicated modal to pick a new incident icon.

* **FR-8.2: Status Bar Feedback**
  * A bottom-center floating pill shall report operational status and diagnostics:
    * Connection states: `Waiting for sheet URL…`, `Detecting columns…`, `Loading geocoder…`, `Fetching data…`.
    * Polling results: Timestamp of last successful fetch, total incident count, open incident count, closed incident count, and count of unmatched addresses (e.g., `Last update: 12:00:00 PM — 5 incident(s): 3 open, 2 closed, 1 unmatched`).
    * Error messages: Informative network and parsing error messages.

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

---

## 5. Build, Quality & CI/CD Pipeline

* **FR-10.1: Code Quality & Linting**
  * JavaScript within `index.html` shall be validated using ESLint with HTML plugin rules (`npm run lint`).
  * Python scripts shall be tested using `unittest` (`python -m unittest discover tests`).

* **FR-10.2: Continuous Deployment**
  * GitHub Actions (`deploy-pages.yml`) shall run ESLint and Python tests on every push and pull request.
  * On commits merged into `main`, the workflow shall automatically execute `fetch_addresses.py` with the Pine Mountain Club bounding box (`34.8,-119.2,34.9,-119.1`) to build `addresses.json` and publish the site to GitHub Pages.
