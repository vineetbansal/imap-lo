;
; $Id: spin_lookup.pro 3877 2009-01-02 23:26:34Z gbc $
;
; pro spin_to_doy_via_osbdb
;
; Procedure(s) to convert spins into other times, whatever, ...
;

;
; Use ibex_spins to do the lookup from an array of spins
; into DOY using the spin database.  Since IDL is such a
; piece of crap, we'll use -1 to get 0 values for frac'n'from.
;
pro spin_to_doy_via_osbdb,	$
    osbdb,			$ ; IN: name of osbdb database
    spins,			$ ; IN: array of spins
    doys,			$ ; OUT: doys
    frac=frac,			$ ; IN: digits in excess of 3, inc .
    type=type,                  $ ; IN: a replacement for Q
    from=from                     ; IN: a replacement for 5


    if (not keyword_set(frac)) then frac=3
    if (not keyword_set(type)) then type='Q'
    if (not keyword_set(from)) then from=5
    if (frac lt 0) then frac=0
    if (from lt 0) then from=0

    args = [ 'ibex_spins', '-d', osbdb, '-R', type, string(spins) ]
    ; print,args
    spawn,args,result,error,/noshell,/null_stdin
    ; print,result
    ; print,error
    doys=strmid(result,from,3+frac)
    ; print,doys
end

;
; eof
;
