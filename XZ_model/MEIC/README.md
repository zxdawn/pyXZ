# MEIC

Mapping MEIC nc files to WRF-Chem chemistry (MOZCART)

## Structure

- src

  - mozart.py

    Main script of data processing.

  - plot_wrfchemi.py

    Plot the quickview of generated wrfchemi* file.

  - conversion_table.csv

    Table of converting MEIC species to WRF-Chem species.

  - hourly_factor.csv (Optional)

    Houly factors to distribute hourly emissions.

- input_files

  - geo_em.d\<n\>.nc

  - ├── \<yyyy\>

    ├     ├── CB05

    ├     ├── ├── \<yyyy\>_\<mm\>\_\_agriculture\_\_CB05*.nc

    ├     ├── RADM2

    ├     ├── ├── \<yyyy\>_\<mm\>\_\_agriculture\_\_RAMD2*.nc

    ├     ├── SAPRC07

    ├     ├── ├── \<yyyy\>_\<mm\>\_\_agriculture\_\_SAPRC07*.nc

    ├     ├── SAPRC99

    ├     ├── ├── \<yyyy\>_\<mm\>\_\_agriculture\_\_SAPRC99*.nc

- output files

  - wrfchemi\_00z\_d<domain>
  - wrfchemi\_12z\_d<domain>

## Example

<img src="https://github.com/zxdawn/pyXZ/raw/master/XZ_model/MEIC/emission_example.png" width="400">