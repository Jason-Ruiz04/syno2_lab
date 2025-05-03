(March 31 to April 02 Storm Outbreak)
-Reads a SPC storm report csv file and makes a code which plots storm reports on a Cartopy map
-Makes a time sequence of these storm reports every hour for 48 hours
-Plots reanalysis data for the date of the case study (downloaded on Era5) of the aforementioned variables.
-Makes a time sequence overlaying the storm reports and the variable data from era5 data from March 31, 2023, to April 02, 2023
-Makes a code which runs a for loop through each variable and produces 48 time sequence plots for each variable.
-Incorporates a function which makes 4 gifs of all the outputs.
If you want to change it to wind or tornado reports, just make sure to direct it to the correct csv file. 
Example:
230331_rpts_filtered_torn.csv
230331_rpts_filtered_wind.csv
230401_rpts_torn.csv
230401_rpts_wind.csv

If you would like to see hail reports for this case study or any storm reports for a different time, you will need to download new 
CSV files and Reanalysis data of your choosing. The code will work with era5 data and archived CSV files from SPC.

