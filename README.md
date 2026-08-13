Instructions for updating quicklook pipeline and re-generating maps using SPICE.

Remove all existing files downloaded using imap-data-access and redownload - this is time-consuming but necessary. The version scheme has changed, so existing files may incorrectly be intepreted as "latest" even when more recent files exist at SDC. This is why the move_crap.sh scripts have also been slightly modified to work with the new scheme as well.

1. Make sure the environment variable IMAP_DATA_DIR is setup correctly. The "imap/lo" folder lives inside it.

   This is likely /Users/nschwadron/Computer/IMAP_Lo/quickpipeline/data going by the quicklook code.
   export IMAP_DATA_DIR=/Users/nschwadron/Computer/IMAP_Lo/quickpipeline/data

2. Trash everything in $IMAP_DATA_DIR/imap/lo, because newer (released) files have a completely different naming scheme than before. SKIP THIS IF YOU HAVE RUN #4 BEFORE.

   cd $IMAP_DATA_DIR/imap/lo
   rm -rf *

3. Make sure you have the latest version of imap-data-access and imap_processing in the activated environment (otherwise imap-data-access will refuse to download files with the latest naming scheme).

   python -m pip install imap-data-access --upgrade
   python -m pip install imap_processing --upgrade

4. Fetch Data

   fetchLoGtInputs.sh has been modified slightly to work with $IMAP_DATA_DIR instead of a previously hardcoded folder. It now also downloads l1b goodtimes cdfs. TAKES A COUPLE OF HOURS.

   cd quicklook
   ./fetchLoGtInputs.sh 20251101 20260813

5. Copy data from $IMAP_DATA_DIR to the several input_* folders, and empty out the output/ and outdir/ folders for stages 1S4, 3S5-3S8.

   ./stageLoGtInputs.sh --clean

6. Generate pointing_file.csv for 3S2, and copy to the rest of the places it is used:

   python scripts/generate_pointing_file.py --pset-dir input_l1c --out 3S2_l1b_quickmaps/config_files/pointing_file.csv
   cp 3S2_l1b_quickmaps/config_files/pointing_file.csv 3S3_l1b_Oxy_quickmaps/config_files
   cp 3S2_l1b_quickmaps/config_files/pointing_file.csv 3S5_l1b_ram_maps/config_files
   cp 3S2_l1b_quickmaps/config_files/pointing_file.csv 3S6_l1b_oxy_ram_maps/config_files

7. Keep only the input files in input_* folders within a repoint range (specified in selectDateRange.sh), and move everything else to an "outside_range" folder inside the input_* folders:

   First bring everything back into input_* folders if they had been moved out earlier.

   ./selectDateRange.sh --restore

   Now run it for real.

   ./selectDateRange.sh

8. Run 1S4 (goodtimes/background rates) as you normally would (takes ~30 mins):

   ./update_goodtimes.sh -1

9. Replace goodtimes csv generated (imap_lo_goodtimes_2.csv) for 3S2 with one generated directly from l1b goodtimes. Copy at other places it is used.

   python scripts/generate_goodtimes_file.py --out 3S2_l1b_quickmaps/config_files/imap_lo_goodtimes_2.csv
   cp 3S2_l1b_quickmaps/config_files/imap_lo_goodtimes_2.csv 3S3_l1b_Oxy_quickmaps/config_files
   cp 3S2_l1b_quickmaps/config_files/imap_lo_goodtimes_2.csv 3S5_l1b_ram_maps/config_files
   cp 3S2_l1b_quickmaps/config_files/imap_lo_goodtimes_2.csv 3S6_l1b_oxy_ram_maps/config_files

10. Run steps 3S5-3S8 (build maps)

    ./update_3s5_3s8.sh

11. Generate a CDF from a map directory (plottable in CAVA or comparable with an SDC map using #12 below).

    python scripts/maps_to_l2_cdf.py --maps-dir 3S5_l1b_ram_maps/outdir/pivot_90/maps --template scripts/template.cdf --out-dir map_cdf/

12. Plot diff plots against official SDC maps.

    Place map CDFS from SDC pipeline (will be soon obtainable through imap-data-access as an l2 product) in a folder, and run comparison plots
    against quicklook maps (map CDFs are lined by by name).

    python scripts/plot_l2_map.py /path/to/sdc/map/cdfs ./map_cdf --output map_compare/
    