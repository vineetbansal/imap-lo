; $Id: 2009-11-30 nas $
;
; pro read_me_bin_map
;
; This procedure reads in a data file 
; and populates arrays that can then 
; be used to do stuff (e.g., fitting)
;
; me_bin_maps are typically set up
; so that each row of data corresponds
; to another latitude. Since this uses
; the intrinsic IDL  read_ascii_data_array
; function, the matrix has the format
;   
; matrix = array(n1    , n0  )
;        = array(jcol  , irow)
; where
;
; row_value  =  vector0[irow] (aka, vector 0)
; col_value =   vector1[jcol] (aka, vector 1) 
;
pro read_me_bin_map,          $
    datafile,          $ ; IN: name of data file for map
    matrix,            $ ; OUT: data matrix
    vector0,           $ ; OUT: vector of row grid at cell centers
    vector1,           $ ; OUT: vector of column grid at cell centers
    n0=n0,             $ ; OUT: number of rows
    n1=n1                ; OUT: number of columns

    compile_opt HIDDEN, STRICTARR

    ds=get_me_bin_header_size(datafile)
    data=read_ascii(datafile,delimiter=' ',header=hdr,data_start=ds)
    matrix=read_ascii_data_array(datafile,' ',ds,data)

    parse_me_bin_header,hdr,lim0,n0,t0,lim1,n1,t1,dl,desc

    colmin = float(lim1[0]) + float(lim1[1]-lim1[0])/(2.0*n1)
    colmax = float(lim1[1]) - float(lim1[1]-lim1[0])/(2.0*n1)
    if (n1 gt 1 ) then begin
        vector1 = colmin + (colmax-colmin)*findgen(n1)/(n1-1.0)
    end else begin
        vector1 = [colmin]
    end

    rowmin = float(lim0[0]) + float(lim0[1]-lim0[0])/(2.0*n0)
    rowmax = float(lim0[1]) - float(lim0[1]-lim0[0])/(2.0*n0)
    if (n0 gt 1) then begin
        vector0 = rowmin + (rowmax - rowmin)*findgen(n0)/(n0-1.0)
    end else begin
        vector0 = [rowmin]
    end

return
end

