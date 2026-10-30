;
; $Id: me_bin_map_io.pro nas $
;
; pro me_bin_map_io
;
; This procedure reads in a map file and writes the output to 
; a three column array: lat, lon, value
;
pro me_bin_map_io,               $
        ips,                     $ ; IN: common isoc plotting structure
        datafile,                $ ; IN: name of the data file
        ofile=ofile                ; IN: output data file                         

        compile_opt HIDDEN, STRICTARR

        if not keyword_set(ofile) then ofile='coldat.txt'

	; get the data and scale it
	ds=get_me_bin_header_size(datafile)
	data=read_ascii(datafile,delimiter=' ',header=hdr,data_start=ds)
	df=read_ascii_data_array(datafile,' ',ds,data)

	;
	; get the magic numbers to set up geometry
	; and establish the spherical mapping
	;
	parse_me_bin_header,hdr,lim0,n0,t0,lim1,n1,t1,dl,desc
	parse_me_bin_extra,ips,hdr

        ;
        ;
	xxx=(0.5+findgen(n1))*(lim1[1]-lim1[0])/n1 + lim1[0]   ; ra  values
	branch = where(xxx gt 180)
	xxx[branch] = xxx[branch] - 360
	if (ips.inside eq 1) then xxx = reverse(xxx)
	yyy=(0.5+findgen(n0))*(lim0[1]-lim0[0])/n0 + lim0[0]   ; dec values
	;
	lat = replicate(1.0, n1) # yyy  ; spray dec value around each lat line
	lon = xxx # replicate(1.0, n0)  ; spray ra  value around each lon line
        ;

        openw, unit, ofile, /get_lun, error=doh
        if (doh ne 0) then return

        for i=0,n1-1 do begin
            for j=0,n0-1 do begin
                printf, unit, yyy[j],xxx[i],df[i,j]
            end
        end

        close, unit
        free_lun, unit
end

;
; eof
;
