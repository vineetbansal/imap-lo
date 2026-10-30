;
; $Id: 
;
; pro plot_vars
; 
; Some simple routines for plotting
; Feed it a datafile and get a plot!
; 
pro plot_vars,                 $
          ips,                 $ ; IN: common isoc plotting structure
          datafile,            $ ; IN: name of the data file
          position=position,   $ ; IN: plotting window (!{xy}.window)
          xvar=xvar,           $ ; IN: x-var to be plotted
          vars=vars,           $ ; IN: array of y-vars to be plotted
          lines=lines,         $ ; IN: linestyles to be used
          colors=colors,       $ ; IN: colors for linestyles
          psyms=psyms,         $ ; IN: psym styles to use 
          xtitle=xtitle,       $
          ytitle=ytitle,       $
          title=title,         $
          missing_value=missing_value, $ ; IN: missing value 
          mono=mono,           $ ; IN: flag to indicate monotonically increasing data
          xtime=xtime            ; IN: flag if label_date is to be used
                                 ;     the value gives the level
                                 ;     = 1: min:seconds
                                 ;     = 2: add hour level  
                                 ;     = 3: add date                           

if not keyword_set(xvar) then xvar = 0

if not keyword_set(xtime) then begin
  parse_variable_file, ips, datafile, titles, df 
  x = df[xvar,*]
end else begin
  parse_variable_file, ips, datafile, titles, df, dcols=[xvar+1],vdbl=date_time 
  x = date_time[xvar,*]
end

nx = n_elements(x)

if keyword_set(mono) then begin
    ips.xrange=[x[0],x[nx-1]]
    ind = where(x ge x[0] and x le x[nx-1])
    x = x[ind]
    df = df[*,ind]
end


nvars = n_elements(titles)
nyvar = nvars-1

if not keyword_set(vars) then vars = 1+ indgen(nyvar)

if keyword_set(xtime) then begin
    formats = ['%H:%I:%S','%H:%I','%M%D','%N/%D!C%Y']
    date_label = label_date(DATE_FORMAT = formats[xtime[*]-1])  
    labels = ['LABEL_DATE', 'LABEL_DATE', 'LABEL_DATE', $
              'LABEL_DATE']
    units = ['Time', 'Hour', 'Day', 'Day'] 
    !x.tickformat=labels[xtime[*]-1]
    !x.tickunits=units[xtime[*]-1]
;    !x.ticklayout = 2    
    titles[xvar] = 'Date'
;    !x.tickinterval = 5  
end

nplot = n_elements(vars)
if not keyword_set(colors) then begin
    colors = 10.0 + 230.0*findgen(nplot)/(nplot-1.0+0.1)
    colors[0] = ips.fg[0]
end

if not keyword_set(psyms) then begin
    psyms = intarr(nyvar)
    psyms[*] = 0
end

if not keyword_set(lines) then begin 
    lines = intarr(nyvar)
    lines[*] = 0
end

if (ips.yrange[0] eq ips.yrange[1])  then begin
    ymin = min(df[vars[0],*],/NAN)
    ymax = max(df[vars[0],*],/NAN)
    if (nplot gt 1) then begin
        for i=1,nplot-1 do begin
            ymin = min([ymin,min(df[vars[i],*],/NAN)],/NAN)
            ymax = max([ymax,max(df[vars[i],*],/NAN)],/NAN)
        end
    end

    range = ymax-ymin

   ips.yrange=[ymin-range/5.0,ymax+range/2.0]
;   print, ips.yrange
end

if not keyword_set(xtitle) then xtitle=titles[xvar]
if not keyword_set(ytitle) then ytitle=titles[vars[0]]
if not keyword_set(title) then title=ips.mapdesc

plot,x, df[vars[0],*], linestyle=lines[0], color=colors[0], $
  xlog=ips.xlog,ylog=ips.ylog,xrange=ips.xrange,yrange=ips.yrange, $
  xstyle=ips.xstyle, ystyle=ips.ystyle,psym=psyms[0],              $
  thick=ips.thick, xtitle=xtitle, ytitle=ytitle, $
  title=title, symsize=ips.symsize,xthick=ips.xthick, $
  ythick=ips.ythick, position=position

if (nplot gt 1) then begin
    for i=1,nplot-1 do begin
        oplot,x,df[vars[i],*], linestyle=lines[i], color=colors[i], $
          psym=psyms[i], symsize=ips.symsize, thick=ips.thick
    end
    
    if (not ips.nolegend) then begin
        items = strarr(nyvar)
        items = titles[vars[0:nplot-1]]
        
        legend,items,psym=psyms[0:nplot-1], $
          linestyle=lines[0:nplot-1],colors=colors[0:nplot-1], $
          thick=ips.thick
                
    end ; if not ips.nologend (ie., draw legend)
end ; if nvars > 1

return
end

;
; oplot_vars
;

pro oplot_vars,                 $
          ips,                 $ ; IN: common isoc plotting structure
          datafile,            $ ; IN: name of the data file
          xvar=xvar,           $ ; IN: x-var to be plotted
          vars=vars,           $ ; IN: array of y-vars to be plotted
          lines=lines,         $ ; IN: linestyles to be used
          colors=colors,       $ ; IN: colors for linestyles
          psyms=psyms,         $ ; IN: psym styles to use                 
          labels=labels,       $ ; IN: label names                      
          missing_value=missing_value ; IN: missing value 

if not keyword_set(xvar) then xvar = 0

if not keyword_set(xtime) then begin
  parse_variable_file, ips, datafile, titles, df 
  x = df[xvar,*]
end else begin
  parse_variable_file, ips, datafile, titles, df, dcols=[xvar+1],vdbl=date_time 
  x = date_time[xvar,*]
end

nx = n_elements(x)

nvars = n_elements(titles)
nyvar = nvars-1

if not keyword_set(vars) then vars = 1+ indgen(nyvar)

nplot = n_elements(vars)
if not keyword_set(colors) then begin
    colors = 10.0 + 230.0*findgen(nplot)/(nplot-1.0+0.1)
    colors[0] = ips.fg[0]
end

if not keyword_set(psyms) then begin
    psyms = intarr(nyvar)
    psyms[*] = 0
end

if not keyword_set(lines) then begin 
    lines = intarr(nyvar)
    lines[*] = 0
end

for i=0,nplot-1 do begin
    oplot,x,df[vars[i],*], linestyle=lines[i], color=colors[i], $
      psym=psyms[i], symsize=ips.symsize, thick=ips.thick
end
    
if (not ips.nolegend) then begin
    items = strarr(nyvar)
    if not keyword_set(labels) then $
      items = titles[vars[0:nplot-1]] $
    else $
      items = labels
    
    legend,items,psym=psyms[0:nplot-1], $
      linestyle=lines[0:nplot-1],colors=colors[0:nplot-1], $
      thick=ips.thick
    
end                           ; if not ips.nologend (ie., draw legend)

return
end

