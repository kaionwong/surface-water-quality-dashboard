# Guide to Surface Water Quality Data and Online Tools

**Classification:** Public  
**Published:** November 20, 2025

## Source

Content in this guide is derived from the official "Guide to Surface Water Quality Data and Online Tools" (WQDP Guidelines Document), published November 20, 2025. Original source:

- Guide to Surface Water Quality Data and Online Tools — WQDP Guidelines Document (PDF): https://environment.extranet.gov.ab.ca/apps/WaterQuality/dataportal/Scripts/app/content/docs/WQDP-GuidelinesDocument.pdf

Please refer to the original document for full context and legal disclaimers.

---

## Table of Contents

1. [Background](#background)
2. [WQDP Station Searches](#wqdp-station-searches)
3. [Reporting Tools](#reporting-tools)
4. [Viewing and Downloading Data](#viewing-and-downloading-data)
5. [Trophic Condition of Alberta Lakes](#trophic-condition-of-alberta-lakes)
6. [Codes and Descriptions](#codes-and-descriptions)
7. [Variable Combining](#variable-combining)

---

## Background

EPA and its partners monitor surface water quality in waterbodies across the province. The **Water Quality Data Portal (WQDP)** ([https://environment.extranet.gov.ab.ca/apps/WaterQuality/dataportal/](https://environment.extranet.gov.ab.ca/apps/WaterQuality/dataportal/)) provides tools that can inform data requests, and support the search, view and download of data.

### Data Available on WQDP

- **Sample Class 'A' data:** Collected by EPA staff or partners trained and audited by EPA staff. Authentication of data for samples collected since 1996 follows EPA's verification/validation process.

- **Agency Code '211' samples:** Collected by or for EPA's Surface Water Monitoring group.

For information on EPA's SWQ Monitoring Programs:
- [Ambient Aquatic Ecosystem Health - MER Plan: Alberta Lakes and Reservoirs](https://open.alberta.ca/publications/ambient-aquatic-ecosystem-health-mer-plan-alberta-lakes-and-reservoirs)
- [Water Quality Monitoring Programs](https://open.alberta.ca/publications/9781460141366)
- [Alberta's Environmental Science Program](https://www.alberta.ca/albertas-environmental-science-program.aspx)

### Disclaimer

The data have been subjected to a verification and validation process; however, occasional errors or anomalies may occur. When comparing water quality samples collected over time, be aware of changes and improvements to:
- Field sampling methods
- Measurement qualifiers
- Analytical laboratory methods (e.g., improved method detection limits)

### Contact Information

**For data requests or anomalies:**  
swq.requests@gov.ab.ca

**For technical issues:**  
EPA.WQDPinfo@gov.ab.ca

---

## WQDP Station Searches

The portal displays stations available for search across multiple layers:

- **River or Stream** stations
- **Lake or Reservoir** stations
- **'Other'** layers (less commonly monitored station types: irrigation canals, snow stations, wetlands)

### Search Features

- Turning on administrative boundaries (e.g., Alberta Sub Basins, Watersheds) helps narrow down stations of interest
- The search field is **case-insensitive** and supports searches for full or partial station codes or names
- A single station may have **more than one station code** assigned to it (e.g., profile and composite sampling)
- Selecting a station code on the map opens a bubble with configuration and data access options

---

## Reporting Tools

### Station Inventory

A summary of sample locations and associated metadata, including:

- Latitude and longitude
- Sample matrix (e.g., water, sediment)
- Sample count (approximate number of samples) by decade
- Water quality variable categories (e.g., routine ions, nutrients, metals)

*Note: Sample counts (decadal) are based on water quality variables indicative of each category and are approximate.*

### Data Download

A comprehensive set of variables for view or download, available in:
- **Long format** (one measurement per row) - includes additional metadata columns
- **Wide format** (pivoted) - columns as variables

---

## Long-Term Monitoring Programs

### Long-Term River Network (LTRN)

A well-established core provincial monitoring program for Alberta's major rivers, several of which cross interprovincial and international boundaries.

- **30+ stations** located along 13 river systems
- **Monthly samples** identified by project codes with format `ABS*34`
- Includes additional samples collected outside regular monitoring program

### Tributary Monitoring Network (TMN)

A core program monitoring water quality of tributaries contributing to Alberta's major rivers.

- **70+ monitoring stations** on tributaries
- **Monthly samples** in addition to enhancement samples
- Dataset includes samples collected outside regular monitoring program

For further information: [Water Quality Monitoring Programs](https://open.alberta.ca/publications/9781460141366)

---

## Lake and Reservoir Data

Data collection from approximately **30 lakes and reservoirs** occurs annually. Data are available in two forms:

1. Raw water quality data
2. Summary format of lake condition (table or graph)

For information: [Ambient Aquatic Ecosystem Health - MER Plan](https://open.alberta.ca/publications/ambient-aquatic-ecosystem-health-mer-plan-alberta-lakes-and-reservoirs)

### Raw Water Quality Data Types

- **Whole-lake (composite) samples:** Multiple sub-samples of the upper water column taken throughout the lake (basin), combined to determine overall water quality conditions during open-water period (May to October)

- **In situ measurements:** Temperature, specific conductivity, dissolved oxygen, and pH taken at the deepest area (profile station) with electronic meter at specific depth intervals

- **Profile station samples:** Collected at specific depths

- **Grab station samples:** Collected at one location on the lake/reservoir

---

## Trophic Condition of Alberta Lakes

### Summary of Lake Condition

Lake condition is often based on the level (or concentration) of 2 key trophic indicators:

- **Total Phosphorus:** A key nutrient
- **Chlorophyll-a:** A general measure of algal biomass

These measurements group Alberta lakes into trophic categories based on biological productivity:

- **Oligotrophic:** Low productivity
- **Mesotrophic:** Moderate productivity
- **Eutrophic:** High productivity
- **Hyper-eutrophic:** Very high productivity

*Note: These categories (based on the 1982 OECD publication "Eutrophication of Waters: Monitoring Assessment and Control") have been used in Alberta since the 1980s and are commonly used worldwide.*

### Trophic Condition Tool

A summary of lake condition by trophic category, determined by calculating the overall mean (from each lake's annual average) of total phosphorus or chlorophyll-a concentrations for lakes with at least three composite samples in any single year (May to October).

### Trophic Data: Annual Mean Concentrations

Annual trophic data (total phosphorus, chlorophyll-a, and secchi depth) for individual lakes.

---

## Viewing and Downloading Data

### Accessing Data for Single Station

- Select the station on the map
- The bubble contains links to reporting tools for downloading station inventory and measurement data

### Accessing Data for Multiple Stations

- Use the **multi-point select function** to export inventory or measurement data for up to 2,000 stations across a map layer
- Use the **data download link** located under the SWQ DATA tab to export measurement data for one or many stations for a specific station type

---

## Data Download Details

### Download Format Options

The download report is available in:

- **Long format** - Contains additional columns of metadata (one measurement per row)
- **Wide format** - Pivoted format for easier spreadsheet analysis

### Download Requirements

All filter or search categories (except date fields) are required to produce a report. Nested filters must be applied in top-down order.

### Important Notes

- Reports are **limited to one station type per download** (rivers, lakes, or 'Other' station type)
- Reports are **station-centric**
- LTRN and TMN datasets include enhancement samples; use sample codes to filter for regular monthly monitoring only
- **Maximum row limit for Excel export:** 1,048,576 rows
- For large datasets, get an initial record count to determine if the limit is exceeded

### User Variable Groups (UVGs)

User Variable Groups represent analytical scans requested for laboratory analysis:

- **INORGANICS NO METALS** is the exception - includes field readings, observations, and variables from multiple analytical packages (routine, nutrients, bacteriological, chlorophyll, isotopes)

**Note:** Some organic variables are reported under more than one analytical scan and belong to multiple UVGs. Check "Crossover Variables in UVG Lists" for comprehensive variable coverage.

### Valid Method Variables (VMV)

VMV codes are unique combinations of:
- Variable
- Method of analysis or measure
- Unit of measure
- Method detection limit

The same variable name can be reported under different VMV codes due to different analytical methods or method detection limits.

---

## Field Observations and Measurements

### Field Observations

In addition to field measurements, downloads include field observations pertaining to the water body or sample:

- **Flow, Turbidity, Colour, Foam:** 0=Absent, 1=Low, 2=Moderate, 3=High
- **Odour:** 0=Absent, 1=Present

### Measurement Qualifiers and Comments

Qualifiers and comments provide additional information about measurements:
- Hold time exceedances
- Sample dilutions
- Suspect values

The majority of qualifiers are added during EPA's validation of preliminary data. See "Validation Rules and Procedures" for further information.

---

## Codes and Descriptions

### Station Number Format

Station numbers have the format: **AB05CE0350**

- **AB** = Province
- **05** = Continental river basin
- **CE** = Sub-basin
- **Last 4 digits** = Arbitrarily assigned (number order does not determine upstream to downstream locations)

See **River Basin and Sub-basin Codes** for reference.

### Transect Stations

Originally, each sampling point across a transect was assigned a separate station number (e.g., Right Bank, Centre, Left Bank).

Since 2009, transects are given one station number with additional measurements (e.g., Distance from Right Bank) to identify sampling location.

*Note: Station combining is underway. Combined transects will contain 'Transect' in the station description.*

### Station Name and Description

Surface water station numbers are composed of:
- **Station Name:** General description of sampling location (e.g., "North Saskatchewan River")
- **Station Description:** Specific information about the sampling site (e.g., "at Devon")

### Key Codes

- **Sample Matrix:** Numeric value identifying the substance or material sampled (e.g., water, sediment)
- **Collection Code:** Numeric value identifying the water/sediment/biota collection method
- **Sample Type Code:** Numeric value identifying the type of sample (e.g., composite, grab)
- **Station Type Code:** Numeric value identifying the site type (0=Rivers/streams, 1=Lakes, 5=Reservoirs)

See **Sample Codes for Matrix, Collection, Sample type, Lab and Project (LTRN, TMN)** for complete reference.

---

## Variable Combining

### Approach

The data downloads do not employ automatic rules for variable combining. An ongoing qualitative assessment of method comparability is available:

[Qualitative Assessment of Comparability of Laboratory Analytical Method Descriptions - Part 1](https://open.alberta.ca/publications/qualitative-assessment-comparability-of-laboratory-analytical-method-descriptions-part-1)

### Assessment Details

This assessment:
- Compares methods to international standards or scientific literature
- Provides reasons for method comparability or incomparability
- Serves as a reference for internal and external stakeholders
- **Does not** determine final data combining decisions (remains with user or decision maker)

### Note

The assessment speaks to analytical method comparison for elements (including ions and phosphorus). Method comparability assessments for routine, nutrients, and organics are underway.

---

## Excel Notes

When combining measurements in pivoted format:
- **Measurement values must be converted to number format** in Excel for proper flag and measurement calculations
- In long format, **DepthOfSampling** is an attribute (column) for Profile stations; it is a measurement for other station types

---

## Graph Export Recommendation

⚠️ **Note:** It is recommended that **downloading data from graphs be avoided** because:
- Column headers are improperly formatted
- In the Trophic Condition graph, Chlorophyll remains as the column header when Phosphorus is selected
- No control of page breaks when exporting to PDF (portion of station name may flow onto next page)

To navigate back to main page from trophic graph and sub-reports, use the **blue back arrow** in the report header.

---

**Classification:** Public  
**Last Updated:** November 20, 2025

---

## Data Analysis Findings

### VariableName ↔ UnitCode Cardinality

**Analysis date:** May 18, 2026  
**Script:** `check_variablename_unitcode.py`  
**Source:** `data/raw/alberta_surface_water_quality_data.csv` (247,121 rows)

After dropping 22,532 rows with null `VariableName` or `UnitCode`, **77 distinct VariableNames** were examined for their mapping to `UnitCode`.

**Result:** 74 of 77 VariableNames map to exactly one UnitCode. The remaining 3 map to multiple UnitCodes:

| VariableName | UnitCodes |
|---|---|
| CARBON DISSOLVED ORGANIC (DOC) | `mg/L`, `ug/L` |
| FLUORESCENT DISSOLVED ORGANIC MATTER-FDOM (FIELD) | `RFU`, `ppb QSU` |
| SAMPLING DISTANCE FROM LEFT BANK | `%`, `m` |

**Implication:** `VariableName` alone is **not** a reliable key for determining the unit of measure. Use `VmvCode` (which encodes variable + method + unit) or inspect `UnitCode` per-row when working with these three variables. This is consistent with the VMV code design described in the [Valid Method Variables (VMV)](#valid-method-variables-vmv) section above.

---

