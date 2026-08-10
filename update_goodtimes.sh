[ -z "$1" ] || delaytime=$1

cd 1S04_l1b_histRates_autogoodtimes

./driver.sh "$delaytime"
cd output 
cp imap_lo_goodtimes.csv ../../input_goodtime
cp imap_lo_HO_cnts_expo.csv ../../input_goodtime_context
cp imap_lo_goodtimes.csv ../../3S2_l1b_quickmaps/config_files/imap_lo_goodtimes_2.csv
cp imap_lo_goodtimes.csv ../../3S3_l1b_Oxy_quickmaps/config_files/imap_lo_goodtimes_2.csv
cp imap_lo_goodtimes_ideas.csv ../../1S12_TOFideas

cp imap_lo_H_background.csv ../../3S2_l1b_quickmaps/config_files
cp imap_lo_O_background.csv ../../3S3_l1b_Oxy_quickmaps/config_files

cp imap_lo_goodtimes.csv ../../3S5_l1b_ram_maps/config_files/imap_lo_goodtimes_2.csv
cp imap_lo_goodtimes.csv ../../3S6_l1b_oxy_ram_maps/config_files/imap_lo_goodtimes_2.csv
cp imap_lo_H_background.csv ../../3S5_l1b_ram_maps/config_files
cp imap_lo_O_background.csv ../../3S6_l1b_oxy_ram_maps/config_files

cd ..
cd ..

