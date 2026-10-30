; $Id: 2009-11-30 nas $
;
; pro dump_me_bin_map
;
; Dump a map from a matrix and vectors
;
; For debugging, mostly 
; 
pro dump_me_bin_map,   $
    file,              $ ; IN: name of data file for dump
    matrix,            $ ; IN: data matrix
    vector0,           $ ; IN: vector of row grid at cell centers
    vector1,           $ ; IN: vector of column grid at cell centers
    n0=n0,             $ ; IN: number of rows
    n1=n1                ; IN: number of columns

    openw, unit, file, /get_lun, error=doh
    if (doh ne 0) then return

    if not keyword_set(n0) then n0 = n_elements(vector0)
    if not keyword_set(n1) then n1 = n_elements(vector1)

    d0 = vector0[1] - vector0[0] 
    d1 = vector1[1] - vector1[0] 

    printf,unit,"# 20:",string(n0,'(i0)'),"x",string(n1,'(i0)'),":-5.0x-5.0:7x6:0:6"
    printf,unit,"# "
    printf,unit,"# ",systime(0)
    printf,unit,"# "
    printf,unit,"# dump_me_bin_map.pro"
    printf,unit,"# "
    printf,unit,"# "
    printf,unit,"# "
    printf,unit,"#  -0 dec (addresses incr. downwards)"
    printf,unit,"#  -1 ra (addresses incr. left->right)"
    printf,unit,"# "
    printf,unit,"#  h_min=",string(min(matrix),'(f0)'),$
      " h_max=",string(max(matrix),'(f0)'),$
      " h_title='dunno'"
    printf,unit,"#  min_0=",string(vector0[0]-d0*0.5,'(f0)'), $
      " max_0=",string(vector0[n0-1]+d0*0.5,'(f0)')," num_0=",string(n0,'(i0)'), " title_0='rows ' "
    printf,unit,"#  min_1=",string(vector1[0]-d1*0.5,'(f0)'), $
      " max_1=",string(vector1[n1-1]+d1*0.5,'(f0)')," num_1=",string(n1,'(i0)'), " title_1='columns ' "
    printf,unit,"#  desc='dunno'
    printf,unit,"# "
    printf,unit,"# "
    printf,unit,"# "
    printf,unit,"# "
    printf,unit,"###"
    for i=0l,n0-1l do begin
        for j=0l,n1-1l do begin
            printf,unit,matrix[j,i],format='(f15.5," ", $)'
        end
        printf,unit,""
    end


    close, unit
    free_lun, unit

end
