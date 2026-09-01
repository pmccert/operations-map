# PMC CERT Map — Data from Google Sheet

A single-file static web application that displays a Leaflet map centered on
**Pine Mountain Club, CA** and plots live coordinates read from a publicly
accessible Google Sheet.

## Features

* **No server required** — open `index.html` directly in any modern browser, or
  host it on any static file host (GitHub Pages, Netlify, etc.).
* **Google Sheet integration** — on first load the app asks for a Google Sheets
  URL and derives the CSV export URL automatically.
* **Auto-refresh** — the latest coordinate (last data row) is fetched every
  **10 seconds** and plotted on the map.
* **Trail of history** — every previously plotted position is shown as a faded
  blue dot; the most recent position is shown as a larger red dot with a popup.
* **Basemap switcher** — choose from four tile sources via the top-right control:
  * OpenStreetMap
  * OpenTopoMap (hillshaded terrain)
  * USGS Topo
  * USGS Imagery

## Google Sheet format

The sheet must be **publicly readable** (File → Share → Anyone with the link →
Viewer).  It should contain at minimum two columns:

| Column A (x / longitude) | Column B (y / latitude) |
|--------------------------|-------------------------|
| -119.155                 | 34.857                  |
| …                        | …                       |

The first row is treated as a header and skipped.  The **last** data row is
plotted each refresh cycle.

## Usage

1. Open `index.html` in a browser.
2. Paste your Google Sheets URL in the dialog that appears and click **Load Map**.
3. The map will zoom to Pine Mountain Club and begin plotting the latest
   coordinate from the sheet every 10 seconds.
