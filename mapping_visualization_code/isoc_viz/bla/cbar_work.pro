; script for running/testing colorbar stuff

; run resolve_xxx_modules first
;
;.r setup_plot_device
;.r color_scaling
;.r colorbar_ticks
;.r make_me_bin_plot
;;.r make_colorbar
;.r kwproc
;.r my_make_colorbar2

; @resolve_core_modules

ips=set_ips_defaults()
setup_x_device,ips
ips.cbartool='ver2'
;ips.cbartool='orig'
;setup_eps_device,ips & device,file='sample.eps'
;setup_z_device,ips

img0=findgen(100)#findgen(100)+1

img0a=color_scaling(ips,img0)
; t v s c l,img0a,.1,.5,/norm,top=ips.ctop
bimage=bytscl(img0a,top=ips.ctop) + 1
tv,bimage,.1,.5,/norm
;
make_colorbar_xy,ips,ytitle=ips.scaling,position=[.1,.1,.15,.4]

ips.scaling='log'
img0b=color_scaling(ips,img0)
; t v s c l,img0b,.4,.5,/norm,top=ips.ctop
bimage=bytscl(img0b,top=ips.ctop) + 1
tv,bimage,.4,.5,/norm
;
make_colorbar_xy,ips,xtitle=ips.scaling,position=[.4,.2,.6,.3]

ips.scaling='sqrt'
img0c=color_scaling(ips,img0)
; t v s c l,img0c,.7,.5,/norm,top=ips.ctop
ips.scaleopt='cb_scaleformat=g7.2'
bimage=bytscl(img0c,top=ips.ctop) + 1
tv,bimage,.7,.5,/norm
;
make_colorbar_xy,ips,ytitle=ips.scaling,position=[.75,.1,.8,.4]

;device,/close ;for eps
;write_png,'sample.png',tvrd()
;device,/close ;for png

