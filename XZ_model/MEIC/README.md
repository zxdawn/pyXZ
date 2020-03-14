# MEIC

Mapping MEIC nc files to WRF-Chem chemistry (MOZCART)

## Structure

### src

- mozcart.py

  Main script of data processing.

- plot_wrfchemi.py

  Plot the quickview of generated wrfchemi* file.

- conversion_table.csv

  Table of converting MEIC species to WRF-Chem species.

- hourly_factor.csv (Optional)

  Houly factors to distribute hourly emissions.

### input_files

- geo_em.d\<n\>.nc

- ├── \<yyyy\>

  ├     ├── CB05

  ├     ├── ├── \<yyyy\>_\<mm\>\_\_agriculture\_\_CB05*.nc

  ├     ├── ├── \<yyyy\>_\<mm\>\_\_***

  ├     ├── RADM2

  ├     ├── ├── \<yyyy\>_\<mm\>\_\_agriculture\_\_RAMD2*.nc

  ├     ├── ├── \<yyyy\>_\<mm\>\_\_***

  ├     ├── SAPRC07

  ├     ├── ├── \<yyyy\>_\<mm\>\_\_agriculture\_\_SAPRC07*.nc
  
  ├     ├── ├── \<yyyy\>_\<mm\>\_\_***
  
  ├     ├── SAPRC99
  
  ├     ├── ├── \<yyyy\>_\<mm\>\_\_agriculture\_\_SAPRC99*.nc
  
  ├     ├── ├── \<yyyy\>_\<mm\>\_\_***

### output files

- wrfchemi\_00z\_d<domain>
- wrfchemi\_12z\_d<domain>

## Usage

1. Put input files like above

2. Edit several paras:

   ```
   domain = 'd01'
   resample_method='nearest' #nearest or idw
   
   # emission year
   yyyy_emi = 2016
   # simulated date
   # emissions of any day in the month are same
   yyyy = 2019
   mm = 7
   dd = 25
   ```

3. Run the main script:

   ```
   python mozcart.py
   ```

4. Check the log and output files.

## Example

Quick look of one time stamp.

```
python plot_wrfchemi.py
```

Sample file:

<img src="https://github.com/zxdawn/pyXZ/raw/master/XZ_model/MEIC/emission_example.png" width="900">