;Based on code from M A Dayeh 
;Reads IBEX MAP data & plots them in different projections.

pro plot_2col_maps,   $
    ips,              $  ; IN: common plotting environment
    datafiles,        $  ; IN: datafiles to be plotted
    p0lon=lon0,       $  ; IN: longitude at center of plot
    p0lat=lat0,       $  ; IN: latitude at center of plot
    rota=rot0,        $  ; IN: rotation of the plot
    ps=ps0,           $  ; IN: ps={-1-png(zvar), 0-png(zzz), 1-ps, 2-eps}
    mag=mg0,          $  ; IN: Increase to decrease pixelation effects (6 good for pubs)
    rows=rows0,       $  ; IN: number of plots down
    cbranges=cbr0,    $  ; IN: range for colorbars (each row)
    cbtitles=cbt0,    $  ; IN: titles of colorbars (each row)                
    outfile=outfl0,   $  ; IN: filename for output
    labels=labs0,     $  ; IN: got labels?
    xsize=xsize,      $  ; IN: x dimension of x-win
    ysize=ysize,      $  ; IN: y dimension of y-win
    xoff=xoff,        $  ; IN: x-offset for maps position
    yoff=yoff            ; IN: y-offset for maps position

flag_cbr=0
flag_cbt=0
if (not keyword_set(p0lon)) then lon0=255.399429
if (not keyword_set(p0lat)) then lat0=5.098670
if (not keyword_set(rot0) ) then rot0=0.0 
if (not keyword_set(ps0)  ) then ps0 = 0
if (not keyword_set(mg0)  ) then mg0 = 6
if (not keyword_set(rows0)) then rows0 = 2
if (not keyword_set(cols0)) then cols0 = 2
if (not keyword_set(cbr0 )) then flag_cbr = -1
if (not keyword_set(cbt0 )) then flag_cbt = -1
if (not keyword_set(outfl0 )) then outfl0='pmm.png'
if (not keyword_set(labs0 )) then labs0=1
if (not keyword_set(xsize)) then xsize=1280
if (not keyword_set(ysize)) then ysize=960
if (not keyword_set(xoff)) then xoff=0.02
if (not keyword_set(yoff)) then yoff=0.01

!p.multi=[0,cols0,rows0,0,0]
if (ps0 eq 1) then begin
    setup_ps_device,ips
   device,filename=outfl0
end else if (ps0 eq 2) then begin
    setup_eps_device,ips
    device,filename=outfl0
end else if (ps0 eq 0) then begin
    setup_x_device,ips, xsize=xsize, ysize=ysize
end else begin
    print, "ps not set"
end

nmaps = n_elements(datafiles)
for imap=0, nmaps-1 do begin

    datafile=datafiles[imap]

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

    ; long/lat min and max
    lonmin = float(lim1[0]) 
    lonmax = float(lim1[1]) 
    latmin = float(lim0[0]) 
    latmax = float(lim0[1]) 

    ; the following refer to bin centers of the grid
    lonmin_cen = float(lim1[0]) + float(lim1[1]-lim1[0])/(2.0*n1)
    lonmax_cen = float(lim1[1]) - float(lim1[1]-lim1[0])/(2.0*n1)
    latmin_cen = float(lim0[0]) + float(lim0[1]-lim0[0])/(2.0*n0)
    latmax_cen = float(lim0[1]) - float(lim0[1]-lim0[0])/(2.0*n0)

    ; magnify using the magnification factor  
    imsize=SIZE(df)
    magdf = CONGRID(df, mg0*imsize[1], mg0*imsize[2])
    ;for non-pixelated display use ,/interp keyword

    ; rescale image
    if (flag_cbr eq 0) then begin 
        cbr = [cbr0[0,imap/2], cbr0[1,imap/2]]
    end else begin
        if (((imap+1)/2 - (imap+1)/2.0) lt 0.0) then cbr = [1.03*min(magdf), max(magdf)]
    end
    bymdf = bytscl(magdf, min = cbr[0], max = cbr[1], top=ips.ctop)

; initial position
    pos = fltarr(4)
    row = imap/2
    col = imap-row*2

    y0=1.0-(row+1.0)/rows0+yoff
    y1=y0+1.0/rows0-2*yoff
    if col eq 0 then begin
        x0 = xoff
        x1 = 0.5- 2*xoff
    end else if col eq 1 then begin
        x0 = 0.5+ 2*xoff
        x1 = 1 - xoff
    end

    pos[0] = x0
    pos[1] = y0
    pos[2] = x1
    pos[3] = y1

    map_set,lat0,lon0,rot0,name=ips.mapname,/isotropic, $
      /noborder,reverse=ips.inside,$
      pos=pos,/advance,/noerase

    remap = map_image(bymdf,Startx,Starty, xsize, ysize, $
                      COMPRESS=1, LATMIN=latmin, LONMIN=lonmin, $
                      LATMAX=latmax, LONMAX=lonmax)

    if (ps0 gt 0) then remap(where(remap EQ 0B)) = 255B

; Map positioning

    pos[0] = Startx / float(!d.x_vsize)
    pos[1] = Starty / float(!d.y_vsize)
    pos[2] = (Startx + xsize) / float(!d.x_vsize)
    pos[3] = (Starty + ysize) / float(!d.y_vsize)

; Display the map
    imdisp, remap, pos=pos, /usepos, /noscale,background=background

; make the grid
    make_me_bin_map_grid,ips
; make labels if wanted
; fontsize controlled by ips.fs - fontsize; 
;                 ips.mapgridfsd -- delta (-2 default)
    if (labs0) then begin        
        make_me_bin_std_hs,ips,labels,ras,decs,colors
        make_me_bin_overlay,ips,labels,ras,decs,colors
    end


    if (((imap+1)/2 - (imap+1)/2.0) ge 0.0) then begin
        midx = 0.5*pos[0] + 0.5*oldpos[2]
        midy = 0.5*pos[1] + 0.5*pos[3]

        if (flag_cbt lt 0) then begin
            cbtitle = ''
        end else begin
            cbtitle = cbt0[imap/2]
        end 
        
        colorbar, range=cbr, $
          position= [midx, pos[1]+2*yoff,pos[0]-xoff/3, pos[3]-yoff*4] , $
          /vertical,title=cbtitle,charsize=1.5
    end

    oldpos = pos

end


if (ps0 ge 1) then begin
    device,/close
end else if (ps0 eq 0) then begin
    if (strpos(outfl0,'png') < 0 and  $
        strpos(outfl0,'PNG') < 0) then outfl0=outfl0 + '.png'
    
    give_credit_where_due
    image = tvrd(0,0,!d.x_size,!d.y_size,true=1)
    write_png,outfl0,image
end

return
end

;
; For plottng three columns: map1, map2, diff (in red/blue color-scale)
;

pro plot_mmdiff_maps,   $
    ips,              $  ; IN: common plotting environment
    datafiles,        $  ; IN: datafiles to be plotted
    p0lon=lon0,          $  ; IN: longitude at center of plot
    p0lat=lat0,        $  ; IN: latitude at center of plot
    rota=rot0,        $  ; IN: rotation of the plot
    ps=ps0,           $  ; IN: ps={-1-png(zvar), 0-png(zzz), 1-ps, 2-eps}
    mag=mg0,          $  ; IN: Increase to decrease pixelation effects (6 good for pubs)
    rows=rows0,       $  ; IN: number of plots down
    cbranges=cbr0,    $  ; IN: range for colorbars (each row)
    cbtitles=cbt0,    $  ; IN: titles of colorbars (each row)                
    outfile=outfl0,   $  ; IN: filename for output
    labels=labs0,      $  ; IN: got labels?
    xsize=xsize,      $  ; IN: x dimension of x-win
    ysize=ysize,      $  ; IN: y dimension of y-win
    xoff=xoff,        $  ; IN: x-offset for maps position
    yoff=yoff,        $  ; IN: y-offset for maps position
    floors=flrs0,     $  ; IN: array of mins to use for flux differenc inc
    maxdiff=mdif0,    $  ; IN: array of maximum diffs to show
    horizontal=horizontal,  $  ; IN: horizontal colorbar
    vertical=vertical          ; IN: horizontal colorbar

flag_cbr=0
flag_cbt=0
flag_flr=0
flag_cel=0
cols0=3

if (not keyword_set(lon0)) then ln0=255.399429
if (not keyword_set(lat0)) then lat0=5.098670
if (lat0 lt 0.0 ) then lat0=0.0
if (not keyword_set(rot0)) then rot0=0.0 
if (not keyword_set(ps0) ) then ps0 = 0
if (not keyword_set(mg0) ) then mg0 = 6
if (not keyword_set(rows0)) then rows0 = 2
if (not keyword_set(cbr0 )) then flag_cbr = -1
if (not keyword_set(cbt0 )) then flag_cbt = -1
if (not keyword_set(flrs0 )) then flag_flr = -1
if (not keyword_set(mdif0 )) then flag_cel = -1
if (not keyword_set(outfl0 )) then outfl0='pmm.png'
if (not keyword_set(labs0 )) then labs0=0 else labs0=1
if (not keyword_set(xsize)) then xsize=1280
if (not keyword_set(ysize)) then ysize=960
if (not keyword_set(xoff)) then xoff=0.02
if (not keyword_set(yoff)) then yoff=0.01

!p.multi=[0,cols0,rows0,0,0]
if (ps0 eq 1) then begin
    setup_ps_device,ips
   device,filename=outfl0
end else if (ps0 eq 2) then begin
    setup_eps_device,ips
    device,filename=outfl0
end else if (ps0 eq 0) then begin
    setup_x_device,ips, xsize=xsize, ysize=ysize
end else begin
    print, "ps not set"
end

pos = fltarr(4)

nmaps = n_elements(datafiles)
for row=0, rows0-1 do begin

    datafile_lt=datafiles[row*2]
    datafile_rt=datafiles[row*2+1]

    ; get the data and scale it
    ds_lt=get_me_bin_header_size(datafile_lt)
    data_lt=read_ascii(datafile_lt,delimiter=' ',header=hdr_lt,data_start=ds_lt)
    df_lt=read_ascii_data_array(datafile_lt,' ',ds_lt,data_lt)
    
    ds_rt=get_me_bin_header_size(datafile_rt)
    data_rt=read_ascii(datafile_rt,delimiter=' ',header=hdr_rt,data_start=ds_rt)
    df_rt=read_ascii_data_array(datafile_rt,' ',ds_rt,data_rt)

    ;
    ; get the magic numbers to set up geometry
    ; and establish the spherical mapping
    ;
    parse_me_bin_header,hdr_lt,lim0_lt,n0_lt,t0_lt,lim1_lt,n1_lt,t1_lt,dl_lt,desc_lt
    parse_me_bin_extra,ips,hdr_lt

    parse_me_bin_header,hdr_rt,lim0_rt,n0_rt,t0_rt,lim1_rt,n1_rt,t1_rt,dl_rt,desc_rt
    parse_me_bin_extra,ips,hdr_rt

    ; long/lat min and max
    lonmin_lt = float(lim1_lt[0]) 
    lonmax_lt = float(lim1_lt[1]) 
    latmin_lt = float(lim0_lt[0]) 
    latmax_lt = float(lim0_lt[1]) 

    lonmin_rt = float(lim1_rt[0]) 
    lonmax_rt = float(lim1_rt[1]) 
    latmin_rt = float(lim0_rt[0]) 
    latmax_rt = float(lim0_rt[1]) 

    ; the following refer to bin centers of the grid
    lonmin_cen_lt = float(lim1_lt[0]) + float(lim1_lt[1]-lim1_lt[0])/(2.0*n1_lt)
    lonmax_cen_lt = float(lim1_lt[1]) - float(lim1_lt[1]-lim1_lt[0])/(2.0*n1_lt)
    latmin_cen_lt = float(lim0_lt[0]) + float(lim0_lt[1]-lim0_lt[0])/(2.0*n0_lt)
    latmax_cen_lt = float(lim0_lt[1]) - float(lim0_lt[1]-lim0_lt[0])/(2.0*n0_lt)

    lonmin_cen_rt = float(lim1_rt[0]) + float(lim1_rt[1]-lim1_rt[0])/(2.0*n1_rt)
    lonmax_cen_rt = float(lim1_rt[1]) - float(lim1_rt[1]-lim1_rt[0])/(2.0*n1_rt)
    latmin_cen_rt = float(lim0_rt[0]) + float(lim0_rt[1]-lim0_rt[0])/(2.0*n0_rt)
    latmax_cen_rt = float(lim0_rt[1]) - float(lim0_rt[1]-lim0_rt[0])/(2.0*n0_rt)

    ; magnify using the magnification factor  
    imsize_lt=SIZE(df_lt)
    magdf_lt = CONGRID(df_lt, mg0*imsize_lt[1], mg0*imsize_lt[2])

    imsize_rt=SIZE(df_rt)
    magdf_rt = CONGRID(df_rt, mg0*imsize_rt[1], mg0*imsize_rt[2])
    ;for non-pixelated display use ,/interp keyword

    map_lt = magdf_lt
    map_rt = magdf_rt

    g1 = where(magdf_lt eq 0, count1)
    if count1 gt 0 then map_lt[g1] = 0 ; zeroing map2 pixels with map1 empty pixel indices
    if count1 gt 0 then map_rt[g1] = 0
    
    g2 = where(magdf_rt eq 0, count2)
    if count2 gt 0 then map_lt[g2] = 0 ; zeroing map1 pixels with map2 empty pixel indices
    if count2 gt 0 then map_rt[g2] = 0

    ; rescale image
    if (flag_cbr eq 0) then begin 
        cbr = [cbr0[0,row], cbr0[1,row]]
    end else begin
        cbr = [1.02*min(map_lt), max(map_lt)]
    end
    bymdf_lt = bytscl(map_lt, min = cbr[0], max = cbr[1], top=ips.ctop)
    bymdf_rt = bytscl(map_rt, min = cbr[0], max = cbr[1], top=ips.ctop)

; set color_table for the col 0 & 1 using standard in ips

    setup_colormap,ips

; initial position (col 0 - left)
    
    y0=1.0-(row+1.0)/rows0+7*yoff
    y1=y0+1.0/rows0-8*yoff
    x0 = 2*xoff
    x1 = 0.3333 - 2*xoff
    
    pos[0] = x0
    pos[1] = y0
    pos[2] = x1
    pos[3] = y1
    
    map_set,lat0,lon0,rot0,name=ips.mapname,/isotropic, $
      /noborder,reverse=ips.inside,$
      pos=pos,/advance,/noerase
    
    remap = map_image(bymdf_lt,Startx,Starty, xsize, ysize, $
                      COMPRESS=1, LATMIN=latmin_lt, LONMIN=lonmin_lt, $
                      LATMAX=latmax_lt, LONMAX=lonmax_lt)
     
    if (ps0 gt 0) then remap(where(remap EQ 0B)) = 255B

; Map positioning

    pos[0] = Startx / float(!d.x_vsize)
    pos[1] = Starty / float(!d.y_vsize)
    pos[2] = (Startx + xsize) / float(!d.x_vsize)
    pos[3] = (Starty + ysize) / float(!d.y_vsize)

    pos_lt = pos

; Display the map
    imdisp, remap, pos=pos, /usepos, /noscale

; make the grid
    make_me_bin_map_grid,ips

    if (labs0) then begin
        make_me_bin_std_hs,ips,labels,ras,decs,colors
        make_me_bin_overlay,ips,labels,ras,decs,colors
    end

    x0 = 0.3333+ 2*xoff
    x1 = 0.6667 - 2*xoff
    
    pos[0] = x0
    pos[1] = y0
    pos[2] = x1
    pos[3] = y1

    map_set,lat0,lon0,rot0,name=ips.mapname,/isotropic, $
      /noborder,reverse=ips.inside,$
      pos=pos,/advance,/noerase

    remap = map_image(bymdf_rt,Startx,Starty, xsize, ysize, $
                      COMPRESS=1, LATMIN=latmin_rt, LONMIN=lonmin_rt, $
                      LATMAX=latmax_rt, LONMAX=lonmax_rt)

    if (ps0 gt 0) then remap(where(remap EQ 0B)) = 255B

; Map positioning

    pos[0] = Startx / float(!d.x_vsize)
    pos[1] = Starty / float(!d.y_vsize)
    pos[2] = (Startx + xsize) / float(!d.x_vsize)
    pos[3] = (Starty + ysize) / float(!d.y_vsize)

    pos_rt = pos

; Display the map
    imdisp, remap, pos=pos, /usepos, /noscale 

; make the grid
    make_me_bin_map_grid,ips
; make labels if wanted
; fontsize controlled by ips.fs - fontsize; 
;                 ips.mapgridfsd -- delta (-2 default)
    if (labs0) then begin
        make_me_bin_std_hs,ips,labels,ras,decs,colors
        make_me_bin_overlay,ips,labels,ras,decs,colors
    end

    midx = 0.5*pos_lt[0] + 0.5*pos_rt[2]
    midy = 0.5*pos_lt[1] + 0.5*pos_rt[3]

    if (flag_cbt lt 0) then begin
        cbtitle = ''
    end else begin
        cbtitle = cbt0[row]
    end 
        
    if keyword_set(vertical) then     colorbar, range=cbr, $
      position= [midx, pos[1]+2*yoff,pos[0]-xoff/3, pos[3]-yoff*4] , $
      /vertical,title=cbtitle,charsize=1.5 $
    else if keyword_set(horizontal) then colorbar, range=cbr, $
      position= [pos_lt[0]+8*xoff, pos[1]-5*yoff, pos_rt[2]-8*xoff, pos[1]-yoff] , $
      /horizontal,title=cbtitle,charsize=1.5 


; **
; now for the differencing .. this is important!
; **  
  
; set color_table for the col 2 using standard in ips
    
    ips1 = ips
    ips1.ct=33
    setup_colormap,ips1
    
    if (flag_flr lt 0)then begin
        floor = 1.02*min(map_lt)
    end else begin
        floor = flrs0[row]
    end

;Differencing maps calculations:
    diff= ((map_lt>floor)-(map_rt>floor))

    if (flag_cel lt 0)then begin
        mdif = 0.99*max(diff)
    end else begin
        mdif = mdif0[row]
    end

    mini_maxi = mdif*[-1,1]

    g3 = where(diff le mini_maxi[0], count2)
    if count2 gt 0 then diff[g3] = mini_maxi[0]
    g3 = where(diff ge mini_maxi[1], count2)
    if count2 gt 0 then diff[g3] = mini_maxi[1]
    
    ;;;+ Plot the difference map
    bydiff = bytscl(diff, min = 1.02*min(diff), max = max(diff), top=ips.ctop)
    
    x0 = 0.6667 + 2*xoff
    x1 = 1.0 -  2*xoff
    
    pos[0] = x0
    pos[1] = y0
    pos[2] = x1
    pos[3] = y1

    map_set,lat0,lon0,rot0,name=ips.mapname,/isotropic, $
      /noborder,reverse=ips.inside,$
      pos=pos,/advance,/noerase
 
    remap = map_image(bydiff,Startx,Starty, xsize, ysize, $
                      COMPRESS=1, LATMIN=latmin_rt, LONMIN=lonmin_rt, $
                      LATMAX=latmax_rt, LONMAX=lonmax_rt)

    if (ps0 gt 0) then remap(where(remap EQ 0B)) = 255B

; Map positioning

    pos[0] = Startx / float(!d.x_vsize)
    pos[1] = Starty / float(!d.y_vsize)
    pos[2] = (Startx + xsize) / float(!d.x_vsize)
    pos[3] = (Starty + ysize) / float(!d.y_vsize)

    pos_di = pos

; Display the map
    imdisp, remap, pos=pos, /usepos, /noscale 

; make the grid
    make_me_bin_map_grid,ips1

    if (labs0) then begin
        make_me_bin_std_hs,ips1,labels,ras,decs,colors
        make_me_bin_overlay,ips1,labels,ras,decs,colors
    end

    midx = 0.5*pos_di[0] + 0.5*pos_rt[2]
    midy = 0.5*pos_di[1] + 0.5*pos_rt[3]

    cbr = [1.02*min(diff),  max(diff)]
    
    if keyword_set(vertical) then      colorbar, range=cbr, $
      position= [midx, pos[1]+2*yoff,pos[0]-xoff/3, pos[3]-yoff*4] , $
      /vertical,title=cbtitle,charsize=1.5 $
    else if keyword_set(horizontal) then colorbar, range=cbr, $
      position= [pos_di[0]+3*xoff, pos_di[1]-5*yoff, pos_di[2]-3*xoff, pos_di[1]-yoff] , $
      /horizontal,title=cbtitle,charsize=1.5 
  
end ; loop over rows

if (ps0 ge 1) then begin
    device,/close
end else if (ps0 eq 0) then begin
    if (strpos(outfl0,'png') < 0 and  $
        strpos(outfl0,'PNG') < 0) then outfl0=outfl0 + '.png'
    
    give_credit_where_due
    image = tvrd(0,0,!d.x_size,!d.y_size,true=1)
    write_png,outfl0,image
end

return
end
