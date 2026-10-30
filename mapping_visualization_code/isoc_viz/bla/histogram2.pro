;;
;; $Id: histogram2.pro 1376 2008-03-24 20:32:37Z gbc $
;;
;;    histogram2.pro
;;

function earthmotionvec, julianday
earthsunvec=sun_hsea(julianday)
zaxis=[0.,0.,1.]
earthmotionvec= crossp(earthsunvec,zaxis)
x= earthmotionvec[0]
y= earthmotionvec[1]
z= earthmotionvec[2]

magearthmotion= sqrt(x^2+y^2+z^2)
norm= earthmotionvec/magearthmotion
return, norm

end

;===========================================
pro findindexes, vector, thetaind, phiind
;input
; vector: vector in hsea coordinates to convert to indexes
;output
; thetaind, phiind: the theta and phi indexes for 6x6 degree bins in
; spherical coordinates in hsea.
x= vector[0]
y= vector[1]
z= vector[2]
magnitude= sqrt((x^2)+(y^2)+(z^2))
theta= acos(vector[2] /magnitude)/!dtor
phi= atan(y,x)/!dtor

if phi lt 0 then phi += 360.

thetaind= fix(theta/6.0)
phiind= fix(phi/6.0)

;print, 'thetaind', thetaind
end

;===========================================
function insidemagsphere, time

magflag=0

SC_HSEa=SC_HSEa(time)

nose_vec=vec_mag_hsea(0.0,0.0,time);position of the nose of the magnetosphere
nose_dot_sc_pos=nose_vec[0]*sc_hsea[0]+nose_vec[1]*sc_hsea[1]+nose_vec[2]*sc_hsea[2]
nose_vec_magnitude=SQRT(nose_vec[0]^2.0+nose_vec[1]^2.0+nose_vec[2]^2.0)
sc_hsea_magnitude=SQRT(SC_hsea[0]^2.0+SC_hsea[1]^2.0+SC_hsea[2]^2.0)
nose_dot_sc_norm=nose_dot_sc_pos/(sc_hsea_magnitude*nose_vec_magnitude)
angle_off_nose=acos(nose_dot_sc_norm)/!dtor
magneto_distance=r_mag(angle_off_nose)

if magneto_distance ge sc_hsea_magnitude then magflag=1.0

return, magflag 

end

;===========================================
pro plot_histogram, map, duration, scaleType, minval, maxval, useZbuff, filename, debug
;swap x and y axies for ploting function
plotablemap = fltarr((duration), 60)
for i=0, 59 do begin
    for j=0, ((duration)-1) do begin
        plotablemap[j,i] = map[i,j]
    endfor
endfor

y=findgen(60)+.5
x=findgen(duration)+.5    ; add 1/2 day to shift graph correctly

;max and min values for the plotted data
if minval eq -1 then pmin = min(plotablemap) else pmin = minval
if maxval eq -1 then pmax = max(plotablemap) else pmax = maxval

for i=0, 59 do begin
   for j=0, (duration)-1 do begin
       if plotablemap[j,i] ge pmax then plotablemap[j,i]= pmax
       if plotablemap[j,i] le pmin then plotablemap[j,i]= pmin
   endfor
endfor    

if debug ne 0 then print, 'pmax=', pmax, 'pmin=', pmin

; setup gfx device
if not keyword_set(useZbuff) then useZbuff = 0
if (useZbuff eq 0) then begin
   set_plot,'x'
   window,0,retain=2
   device,true=24
   device, decomposed = 0
   loadct, 39, /silent
endif else begin
   set_plot,'z'
   loadct, 39, /silent
   ;!P.Charsize=0.9
   device, z_buffering=0, set_resolution=[700,400], SET_PIXEL_DEPTH=24, decomposed=0
endelse

; logic for if we need to rescale z-axis (auto: log if difference is over
; 3 orders of magnitude)
if (scaleType eq 1) or ( (scaleType eq 0) and (pmax - pmin) gt 1000 ) then begin
   ;log
   log_flag = 1
   z = (255*(( alog10(plotablemap/(pmin) )/(alog10((pmax)/pmin))))) 
endif else begin
   ;linear
   log_flag = 0
   z= (255*((plotablemap-pmin)/(pmax-pmin)))
endelse


;needs to be cleaned up a bit
if log_flag eq 1 then begin
   color_plot, z, x, y, ZRANGE=[pmin,pmax], /FILL, TITLE='Counts', XTITLE='Orbit Durration (days)',  YTITLE="Degrees from Earth's Motion",  STITLE='Counts per Bin', /ZCOLORS, /LOGSC
endif else begin
   color_plot, z, x, y, ZRANGE=[pmin, pmax], /FILL, TITLE='Counts', XTITLE='Orbit Durration (days)', YTITLE="Degrees from Earth's Motion", STITLE='Counts per Bin', /STICKV, /ZCOLORS
endelse

image = TVRD(0,0,!D.x_size,!D.y_size,true=3)
WRITE_JPEG, filename, image, QUALITY=100, TRUE=3

end

;=================================================================================
pro histogram, energyband, start_month, start_day, start_year, stop_month=stop_month, stop_day=stop_day, stop_year=stop_year, use_data_set=use_data_set, showmagsphere=showmagsphere, scaling=scaling, minValue=minValue, maxValue=maxValue, Z_Buffer=Z_Buffer, output_file_name=output_file_name, debug=debug

; set default values of optional parameters
if not keyword_set(debug) then debug = 0
if debug ne 0 then debug = 1

if not keyword_set(stop_day) then begin
    stop_day = start_day + 1
    stop_month = start_month
    stop_year = start_year
 endif

if not keyword_set(use_data_set) then use_data_set = 1
if use_data_set lt 0 or use_data_set gt 1 then use_data_set = 1

if not keyword_set(showmagsphere) then showmagsphere = 1
if showmagsphere ne 0 then showmagsphere = 1

if not keyword_set(scaling) then scaling = 0
if scaling lt -1 or scaling gt 1 then scaling = 0

if not keyword_set(minValue) then minValue = -1
if not keyword_set(maxValue) then maxValue = -1
minValue = float(minValue)
maxValue = float(maxValue)

if keyword_set (Z_Buffer) then Z_Buffer = 1 else Z_Buffer = 0

if not keyword_set(output_file_name) then output_file_name="histogram2.jpg"

if debug ne 0 then print, start_month, start_day, start_year, stop_month, stop_day, stop_year, showmagsphere, energyband, output_file_name

; get timescale setup

;converts month, day, and year into julian day
startjulianday=julday(start_month,start_day,start_year)
stopjulianday =julday(stop_month, stop_day, stop_year)

currentjulianday = startjulianday
durration = stopjulianday - startjulianday ; durration of the  in days

; define the array of bins
;add check to make sure delta_t is integer multiple of durration
histogrammap=fltarr( 60, fix(durration) ) ; houses the countrates for a given theta,phi

days_run=0
;run loops per day
while currentjulianday lt stopjulianday do begin

    ; finds vector from the earth to the sun
    earthsunvec=sun_hsea(currentjulianday)
    earthmotionvector=earthmotionvec(currentjulianday)
    
    findindexes, earthmotionvector, thetaind, phiind

    pole=fltarr(3)
    polevec=[0.0, 0.0, 1.0]
    
    looktheta = fltarr(60)
    lookphi = fltarr(60)

    ; find the look vectors
    i=3.                        ; start @ 3 to look at middle of bin
    j=0.
    while i lt 360. do begin
        index=i*!dtor

        lookvec= (earthmotionvector*cos(index)) + (polevec*sin(index))


        ;get theta,phi indices of said look vectors
        findindexes, lookvec, thetaind, phiind
        looktheta[j] = thetaind
        lookphi[j] = phiind

        i+=6.
        j++
    endwhile

    ; now get the count rates for one row

    ;    reads in heliospheric count rates from data file
    ;                   eband         tstype  countrate_map   dataset (0 for jacob's data and 1 for merav's data)
    read_countrate, energyband,    0,    countrate_map, dataset=use_data_set
        
    for j=0, 59 do begin
        histogrammap[j, days_run]=countrate_map[looktheta[j],lookphi[j]]

        ; are we in the magnetosphere??, add additional counts
        if (showmagsphere ne 0) then flag= insidemagsphere(currentjulianday) else flag = 0
        
        if flag eq 1 then begin
           ; print, 'test'
                                ; fluxes from the magnetosphere dependant on energy band
            ENA12=5.9E4  ; where do these numbers come from???
            ena09=2.0/3.0*(5.9E4)
            ena07=1.0/3.0*(5.9E4)
            ENA05=2.0E6
            magena=[ena05,ena05,ena05, ena05,ena09,ena07,ena12,ena12,ena12,ena12,ena12,ena12,ena12,ena12]
            
            addflux = magena[energyband]
            histogrammap[j, days_run] += addflux
        endif
    endfor
    

                                                           
    days_run++
    currentjulianday += 1
endwhile

; turn count rate to counts
histogrammap *= 24 * 3600 / 60

; do the plotting
plot_histogram, histogrammap, durration, scaling, minValue, maxValue, Z_Buffer, output_file_name, debug

end
