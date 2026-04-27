;
; $Id: colorbar_ticks.pro 2418 2008-07-20 23:36:12Z gbc $
;
; function data_from_fraction
; function get_colorbar_ticks_default
; function get_colorbar_ticks
; function get_colorbar_ticks_linear
; function get_colorbar_ticks_sqrt
; function get_colorbar_ticks_log
;
; These procedures generate the actual ticks on the colorbars
;

;
; get the value corresponding to f in [0,1]
;
function data_from_fraction,z_minmax,f
	z_range=float(z_minmax[1] - z_minmax[0])
	z=z_minmax[0] + f * z_range
	return,z
end

;
; ticks is number of intervals
; names are the (ticks+1) labels
; values are the (ticks+1) values in [0,1]
;
function get_colorbar_ticks_default,ips,names,values
	ticks=4
	names=replicate('x',5)
	values=[0.0,.25,.50,.75,1.0]
	
	zz=data_from_fraction(ips.smm,values)
	data=color_invert(ips,zz)
	names=string(data,format="(%'%g')")
	return,ticks
end

;
;The following is not ready yet   
;

; this is still in testing stages
function get_colorbar_ticks_linear,ips, names, values
	;finds order of magnitude of both the max and min values
        tmpmax = ips.zmm[1]
        tmpmin = ips.zmm[0]
        j = 0.0
        while abs(tmpmax) gt 10 do begin
            tmpmax = tmpmax/10
            j++
        endwhile
        tmp = 10^j
        
        k =0.0
        while abs(tmpmin) gt 10 do begin
            tmpmin = tmpmin/10
            k++
        endwhile
        tmp1 = 10^k
 
	;scale options for the colorbar
        case ips.scaleopt of
           ;adjusts range of the colorbar to make
           ;it a more friendly range (rounds to the nearest value of 50)
            'set-range' : begin
                ticks = 3
                range = ips.smm[1] - ips.smm[0]
                frac = range/ticks

                ;change max to fit scale
                tmpmax1 = fix(tmpmax)
                while ips.zmm[1]/tmp gt  tmpmax1 do tmpmax1 += .5
                tmpmax2 = tmpmax1*tmp
                              
                ;change min to fit scale
                tmpmin1 = fix(tmpmin)
                while ips.zmm[0]/tmp1 lt tmpmin1 do tmpmin1 -= 1 
                tmpmin2 = tmpmin1*tmp1
            
                ips.smm = [tmpmin2, tmpmax2]
                               
                chngrange = ips.smm[1] - ips.smm[0]
                chngrange = chngrange/tmp
                if chngrange ge 5 then ticks = floor(chngrange/5.) $
                else ticks = floor(chngrange)
                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2
            end
            ;specific values of ticks chosen by the user
            ;(this is just for now, I'll figure out something better for it)
            'strict-3': ticks = 2 
            'strict-4': ticks = 3
            'strict-5': ticks = 4
            'strict-6': ticks = 5
            'strict-7': ticks = 6
            'strict-8': ticks = 7
            'strict-9': ticks = 8
            'strict-10':ticks = 9
            ;finds best value of ticks
            'strict':  begin
                tmpmax1 = fix(tmpmax)
                while tmpmax gt tmpmax1 do tmpmax1 += .5
                tmpmax2 = tmpmax1*tmp
                
                tmpmin1 = fix(tmpmin)
                while tmpmin lt tmpmin do tmpmin1 -= 1
                tmpmin2 = tmpmin1*tmp1
                chngrange = tmpmax2 - tmpmin2

                range = tmpmax - tmpmin
                chngrange = chngrange*10/tmp
                ticks = floor(chngrange/5. +.1)

                if range/3. eq floor(range/3.) then ticks = 3
                ; print,  ticks
                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2
            end
            
            ;default tick value 
            else: begin

                chngrange = tmpmax*tmp - tmpmin*tmp1
                chngrange /= tmp/10
                ticks = floor((chngrange+.5)/5.) 
                if chngrange/3. eq fix(chngrange/3.) then ticks = 3
                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2 
               
            end
        endcase

        names = replicate('x',ticks+1) 
        
        values = fltarr(ticks+1)
        ipsrange = ips.smm[1] - ips.smm[0]
        ex = ipsrange/ticks

	;finds the desired value of data wished to be displayed and then
	;defines where that value lies along the colorbar
        for i = 0, ticks do begin
            exd = ex*i +ips.smm[0]
            ex1 = exd
	    ;divides value to a number less than 10 in order to find nearest
	    ;rounded value
           
            m = 0.0
            while ex1 gt 10 do begin
                ex1 /= 10
                m++
            endwhile
            tmp = 10^m
                      
            ex2 = floor(ex1)
            if ex1 gt ex2 + .5 then ex2 += 1 $
            else if ex1 gt ex2 +.25 then ex2 += .5
            
            ex2 *= tmp
            ex3  = (ex2-ips.smm[0])/ipsrange
            if ex3 lt 0.0 then ex3 = 0.0
            if ex3 gt 1.0 then ex3 = 1.0
            values[i]= ex3 
            
        endfor

	;temporary - makes sure the first and last ticks are at the very
	;            beginning and ending of the colorbar
        if values[0] ne 0.0 then values[0] = 0.0
        if values[ticks] ne 1.0 then values[ticks] = 1.0

        z = data_from_fraction(ips.smm, values)
        data = color_invert(ips, z)
        names = string(data, format="(%'%g')")
        return, ticks
end

function get_colorbar_ticks_sqrt, ips, names, values
	;converts the max and min values to sqrt scale
        tmpmax = ips.zmm[1]
        tmpmin = ips.zmm[0]
        ips.smm = sqrt(ips.zmm)

	;finds order of magnitude for the max and min values        
        j = 0.0
        while abs(tmpmax) ge 10 do begin
            tmpmax = tmpmax/10
            j++
        endwhile
        tmp = 10^j

        k =0.0
        while abs(tmpmin) ge 10 do begin
            tmpmin = tmpmin/10
            k++
        endwhile
        tmp1 = 10^k
        

        case ips.scaleopt of
            ;alters range to rounded values
            'set-range' : begin
                ;change max to fit scale
                tmpmax1 = fix(tmpmax)
                while ips.zmm[1]/tmp gt  tmpmax1 do tmpmax1 += .5
                tmpmax2 = tmpmax1*tmp
                tmpmax3 = SQRT(tmpmax2)
                              
                ;change min to fit scale
                tmpmin1 = fix(tmpmin)
                while ips.zmm[0]/tmp1 lt tmpmin1 do tmpmin1 -= 1 
                tmpmin2 = tmpmin1*tmp1
                tmpmin3 = SQRT(tmpmin2)

                ips.zmm = [tmpmin2, tmpmax2]
                ips.smm = [tmpmin3, tmpmax3]
                
                chngrange = ips.smm[1] - ips.smm[0]
               
                ;changes tick value to adapt to the adjusted range of the scale
                ticks = floor(chngrange*2/sqrt(tmp))
                if (chngrange*10/(3*sqrt(tmp)) eq $
		    floor(chngrange*10/(3*sqrt(tmp)))) then ticks = 3
               
                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2
                if SQRT(tmpmax) - SQRT(Tmpmin) gt 10 then interval = 100 $
                else interval = 10
            end
            ;specific values of ticks chosen by the user
            ;interval is used in order to show specific squared values 
            ;(ex: 100, 64, 36, 1, etc.)
            'strict-3': begin 
                ticks = 2
                if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
                else interval = 10
                end
            'strict-4': begin
                ticks = 3 
               if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
               else interval = 10
            end
            'strict-5': begin
                ticks = 4
                if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
               else interval = 10
            end
            'strict-6': begin
                ticks = 5
                if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
               else interval = 10
            end
            'strict-7': begin
                ticks = 6
                if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
               else interval = 10
            end
            'strict-8': begin 
                ticks = 7
                if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
                else interval = 10
            end
            'strict-9': begin
                ticks = 8
                if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
               else interval = 10
            end
            'strict-10': begin
                ticks = 9
                if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
               else interval = 10
            end
            ;finds best tick value for scale
            'strict': begin
                ;adjusts scale range
                tmpmax1 =sqrt(tmpmax*tmp)
                while ips.smm[1] gt  tmpmax1 do tmpmax1 += 1
                
                tmpmin1 = sqrt(tmpmin*tmp1)
                while ips.smm[0] lt tmpmin1 do tmpmin1 -= 1
                              
                chngrange = tmpmax1 - tmpmin1
                
                ;changes ticks to adapt to the adjusted scale
                ticks = floor(chngrange/sqrt(tmp))
                if (chngrange*10/(3*sqrt(tmp)) eq $
		    floor(chngrange*10/(3*sqrt(tmp)))) then ticks = 3
                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2
                if chngrange lt 10 then interval = 100 else interval = 10
            end
            ;default tick number
            else: begin
                chngrange = ips.smm[1] - ips.smm[0]
                chngrange /= sqrt(tmp)/10
                ticks = floor((chngrange+.5)/5.) 
                if chngrange/3. eq floor(chngrange/3.) then ticks = 3
                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2
                if SQRT(tmpmax) - SQRT(tmpmin) gt 10 then interval = 100 $
                else interval = 10
            end
        endcase       
        
        names = replicate('x', ticks +1)
        values = fltarr(ticks+1)

        ipsrange = ips.smm[1] -ips.smm[0]
        ex =ipsrange/ticks     
        
	;finds the desired value of data wished to be displayed and then
	;defines where that value lies along the colorbar
        
        for i = 0, ticks do begin
            exd = ex*i +ips.smm[0]
            ;change to original data 
            ex1 = exd*exd 
            
            m = 0.0
            while ex1 gt interval do begin
                ex1 /= 10
                m++
            endwhile
            tmp = 10^m
                                
            ;adds another integer to a number that has a fraction 
            ;greater than .5
            ex2 = floor(ex1)
            if ex1 ge ex2 +.51 then ex2 += 1 $
            else if ex1 ge ex2 +.2 then ex2 += .5
            ex2 = ex2*tmp
            ;returns to altered data value
            ex3 = SQRT(ex2)
            ;finds fraction of the range
            ex4 = (ex3-ips.smm[0])/ipsrange
            if ex4 lt 0.0 then ex4 = 0.0
            if ex4 gt 1.0 then ex4 = 1.0
            values[i] = ex4
        endfor
	; temporary - this just makes sure that the last tick mark is set at 1
       if values[0] ne 0.0 then values[0] = 0.0
       if values[ticks] ne 1.0 then values[ticks] = 1.0
       z = data_from_fraction(ips.smm, values)
       data = color_invert(ips, z)
       names = string(data, format="(%'%g')")
       return, ticks        
   end

function get_colorbar_ticks_log, ips, names, values
	;converts max and min values to log10 scale
        ; tmpmax = ips.zmm[1]
        ; tmpmin = ips.zmm[0]
        ; ips.smm = alog10(ips.zmm)
        ;finds order of magnitude of both the max and min values
	tmpmax = 10^ips.smm[1]
	tmpmin = 10^ips.smm[0]
        j = 0.0
        while abs(tmpmax) gt 10 do begin
            tmpmax = tmpmax/10
            j++
        endwhile
        tmp = 10^j

        k =0.0
        while abs(tmpmin) gt 10 do begin
            tmpmin = tmpmin/10
            k++
        endwhile
        tmp1 = 10^k
        
        
        case ips.scaleopt of
            'set-range' : begin
                ;change max to fit scale
                tmpmax1 = fix(tmpmax)
                while ips.zmm[1]/tmp gt tmpmax1 do tmpmax1 += .5
                tmpmax1 *= tmp
                tmpmax2 = alog10(tmpmax1)
                
              
                ;change min to fit scale
                tmpmin1 = fix(tmpmin)
                while ips.zmm[0]/tmp1 lt tmpmin1 do tmpmin1 -= 1 
                tmpmin1 *=tmp1
                tmpmin2 = alog10(tmpmin1)
                
                ips.zmm = [tmpmin1, tmpmax1]
                ips.smm = [tmpmin2, tmpmax2]
                
                chngrange = ips.smm[1] - ips.smm[0]
                ticks = floor(chngrange)
                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2
                ; print, ticks
            end 
            ;specific values of ticks chosen by the user                       
            'strict-3': ticks = 2
            'strict-4': ticks = 3
            'strict-5': ticks = 4
            'strict-6': ticks = 5
            'strict-7': ticks = 6
            'strict-8': ticks = 7
            'strict-9': ticks = 8
            'strict-10':ticks = 9
            'strict': begin
                ;adjusts range
                tmpmax1 = floor(tmpmax)
                while ips.zmm[1]/tmp gt  tmpmax1 do tmpmax1 += 1

                tmpmin1 = floor(tmpmin)
                while ips.zmm[0]/tmp1 lt tmpmin1 do tmpmin1 -= 1
                
                max = alog10(tmpmax1*tmp)
                min = alog10(tmpmin1*tmp1)

                chngrange = max - min
                ticks = floor(chngrange)
                if ticks/3 eq floor(ticks/3) then ticks = 3
                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2
            end
            else: begin
                max = alog10(tmpmax*tmp)
                min = alog10(tmpmin*tmp1)

                chngrange = max - min
                ticks = floor(chngrange)

		; print,ticks,max,min

                while ticks gt 4 do ticks -= 2
                while ticks le 2 do ticks += 2
            end
        endcase       
 
        
         values = fltarr(ticks +1)
         names = replicate('x', ticks +1)
         ipsrange = ips.smm[1] - ips.smm[0]
         ex = ipsrange/ticks
 
	;finds the desired value of data wished to be displayed and then
	;defines where that value lies along the colorbar
         for i = 0, ticks do begin
             exd = ex*i +ips.smm[0]
             ;changes to original data
             ex1 = (10^exd)
             
             m = 0.0 
             while ex1 gt 10 do begin
                 ex1 = ex1/10
                 m++
             endwhile
             tmp = 10^m
             ;rounds data to display number
             ex2 = floor(ex1)
             if ex1 gt ex2 +.5 then ex2 += 1 $
             else if ex1 gt ex2 + .25  then ex2 += .5
             ex2 = floor(ex2*10)
             ex3 = ex2*tmp/10
             ;returns value to altered data    
             ex4 = alog10(ex3)
             ;finds fraction of the range
             ex5 = (ex4-ips.smm[0])/ipsrange
             if ex5 lt 0.0 then ex5 = 0.0
             if ex5 gt 1.0 then ex5 = 1.0 
             values[i] = ex5 
         endfor

	; temporary - just makes sure that the last tick mark is set at 1 and
	;             the first tick mark is set at 0
         if values[ticks] ne 1.0 then values[ticks]= 1.0
         if values[0] ne 0.0 then values[0] = 0.0

         z = data_from_fraction(ips.smm, values)
         data = color_invert(ips,z)
         names = string(data, format="(%'%g')")
         return, ticks

     end
    


;
; a switch allowing later cleverness.
;
function get_colorbar_ticks,ips,names,values
         case ips.scaling of
             'linear': return, get_colorbar_ticks_linear(ips, names, values)
             'sqrt': return, get_colorbar_ticks_sqrt(ips, names, values)
             'log': return, get_colorbar_ticks_log(ips, names, values)
             else: return, get_colorbar_ticks_default(ips,names,values)
         endcase       
end


;
; ignore the junk below this line -- it is an abandoned development thread.
;


;
; figure out some ticks for (zeemm)
;
function ignore_colorbar_tickscale_linear_frac,zeemm,z
	range=float(zeemm[1] - zeemm[0])
	return,(float(z - zeemm[0]) / range)
end
pro ignore_colorbar_tickscale_linear,$
	zeemm,                  $ ; IN: data limits [min,max]
	ticks,                $ ; OUT: number of tick intervals
	names,                $ ; OUT: tick labels (ticks+1)
	tickv                   ; OUT: tick values (0..1)

	sup= (zeemm[1] gt 0) ? 1 : -1
	slo= (zeemm[0] gt 0) ? 1 : -1

	upper= (sup eq 1) ? floor(zeemm[1]*sup) : ceil(zeemm[1]*sup)
	lower= (slo eq 1) ?  ceil(zeemm[0]*slo) : floor(zeemm[0]*slo)
	ptnup= (upper ne 0) ? floor(alog10((upper))) : 0
	ptnlo= (lower ne 0) ? floor(alog10((lower))) : 0

	; figure out how many ticks
	;         0 1   2   3   4   5   6   7   8   9
	ticklist=[0,0,  4,  3,  4,  5,  3,  3,  4,  4]
	del_list=[0,0,0.5,1.0,1.0,1.0,2.0,2.0,2.0,2.0]

	print,'upper:',upper,ptnup
	print,'lower:',lower,ptnlo

	if (ptnup gt ptnlo) then begin
		; upper is most of the range
		signif=upper*(10.^(-ptnup))
		zz=floor(upper*(10.^(1-ptnup)))*(10.^(ptnup-1))*sup
		start=upper
		poten=ptnup
		sign=sup
		factor=10.^ptnup*sup
		print,'up beats lo',signif,zz,factor
	endif else begin
	    if (ptnup lt ptnlo) then begin
		; lower is most of the range
		signif=lower*(10.^(-ptnlo))
		zz=floor(lower*(10.^(1-ptnlo)))*(10.^(ptnlo-1))*slo
		start=lower
		poten=ptnlo
		sign=slo
		factor=10.^ptnlo*slo
		print,'lo beats up',signif,zz,factor
	    endif else begin
		; upper and lower are comparable
		signif=(sup*upper-slo*lower)*(10.^(-ptnlo))
		if (signif lt 0) then signif=-signif
		zz=floor(upper*(10.^(1-ptnup)))*(10.^(ptnup-1))*sup
		start=upper
		poten=ptnup
		sign=sup
		factor=10.^ptnup*sup
		print,'peers',signif,zz,factor
	    endelse
	endelse 
	ticks=ticklist[floor(signif)]
	delta=del_list[floor(signif)]
	if (ticks eq 0) then begin
		ticks=ticklist[floor(signif*5)]
		delta=del_list[floor(signif*5)]
		factor = 0.2*factor
		zz=floor(start*(10.^(1-poten))+5)*(10.^(poten-1))*sign
	endif else begin
		zz=10*floor(zz*0.1)
		zz=floor(start*(10.^(-poten))+.5)
		print,zz
		zz=zz*(10.^(poten))*sign
	endelse
	print,'zznow',zz

	ticks=ticks+2
	tickv=fltarr(ticks+3)
	names=strarr(ticks+3)
	print,'ticks:',ticks
	for ii=0,ticks do begin
		tickv[ii] = colorbar_tickscale_linear_frac(zeemm,zz)
		names[ii] = string(zz,format="(%'%g')")
		if (tickv[ii] lt 0) then begin
			tickv[ii] = 0
			names[ii] = ' ' ;string(zeemm[0],format="(%'%g')")
			; if (ii lt ticks) then ticks = ii + 1
			; break
		endif
		if (tickv[ii] gt 1) then begin
			tickv[ii] = 1
			names[ii] = ' ' ;string(zeemm[1],format="(%'%g')")
			; if (ii lt ticks) then ticks = ii + 1
			; break
		endif
		zz = zz - delta*factor
	endfor

	; names=replicate('@',6)
	print,'ticks:',ticks
	print,'names:',names
	print,'tickv:',tickv
end

;
; eof
;
