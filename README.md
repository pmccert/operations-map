# PMC CERT Incident Map — Data from Google Sheet

A single-file static web application that displays a Leaflet map centered on
**Pine Mountain Club, CA** and shows live emergency incidents read from a
publicly accessible Google Sheet.

## Features

* **No server required** — open `index.html` directly in any modern browser, or
  host it on any static file host (GitHub Pages, Netlify, etc.).
* **Google Sheet integration** — on first load the app asks for a Google Sheets
  URL and derives the CSV export URL automatically.
* **Auto-refresh every 10 seconds** — all rows are re-read; markers are added,
  updated, or removed to match the current sheet contents.
* **Every row is a distinct incident** — each data row is plotted as its own
  marker on the map.
* **Open / Closed status** — incidents marked `closed` (column C) are rendered
  faded and greyscale; open incidents display in full colour.
* **User-selectable icon** — choose from a set of Font Awesome vector icons
  (emergency, fire, medical, vehicle, hazard, search, wildlife, rescue, pin,
  star) in the startup dialog or via the **Change Icon** toolbar button.
* **Basemap switcher** — choose from four tile sources via the top-right control:
  * OpenStreetMap
  * OpenTopoMap (hillshaded terrain)
  * USGS Topo
  * USGS Imagery

## Google Sheet format

The sheet must be **publicly readable** (File → Share → Anyone with the link →
Viewer).  It should contain the following columns (first row = header, ignored):

| Column A — longitude | Column B — latitude | Column C — status | Column D — label (optional) |
|----------------------|---------------------|-------------------|-----------------------------|
| -119.155             | 34.857              | open              | Structure fire on Mil Potrero |
| -119.160             | 34.862              | closed            | Medical assist                |

* **Column C** should contain the text `open` or `closed` (case-insensitive).
  Any value other than `closed` is treated as open.
* **Column D** is an optional free-text description shown in the marker popup.

## Usage

1. Open `index.html` in a browser.
2. Paste your Google Sheets URL in the dialog, select an incident icon, then
   click **Load Map**.
3. All incidents from the sheet are plotted immediately and refresh every 10
   seconds.
4. Click any marker to see its details (label, status, coordinates).
5. Use **Change Sheet** or **Change Icon** in the top-left toolbar at any time.

